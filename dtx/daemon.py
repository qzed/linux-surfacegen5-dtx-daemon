from . import commands as cmd
from . import events
from . import config
from . import device
from . import notify

from .device import Device

import argparse
import asyncio
import logging
import os
import signal


PROC_EXIT_DETACH_COMMENCE = 0
PROC_EXIT_DETACH_ABORT    = 1


async def _run_handler(log, handler, cfg, env=None):
    handler = cfg.path / handler

    log.debug("subprocess start: {}".format(handler))

    proc = await asyncio.create_subprocess_exec(
        program=bytes(handler),
        env=env,
        cwd=cfg.path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    log.debug("subprocess terminated with exit-code {}".format(proc.returncode))

    if stdout:
        stdout = stdout.decode("utf-8")
        log.info("subprocess terminated with stdout:\n{}".format(stdout))

    if stderr:
        stderr = stdout.decode("utf-8")
        log.warning("subprocess terminated with stderr:\n{}".format(stderr))

    return proc.returncode


def _handle_read(dev, handler, queue):
    for evt in dev.read():
        handler(dev, evt, queue)


class EventHandler:
    def __init__(self, cfg):
        self.cfg = cfg
        self.log = logging.getLogger("handler")
        self.detach_in_progress = False
        self.task_detach_scheduled = 0
        self.task_abort_scheduled = 0
        self.task_attach_scheduled = 0
        self.skip_next_abort = False
        self.notif = None

    def __call__(self, dev, evt, queue):
        if isinstance(evt, events.ConnectionChangeEvent):
            if evt.state():
                self.on_connect(dev, evt, queue)
            else:
                self.detach_in_progress = False
                self.on_disconnect(dev, evt, queue)

        elif isinstance(evt, events.OpModeChangeEvent):
            self.on_op_mode_change(dev, evt, queue)

        elif isinstance(evt, events.DetachButtonEvent):
            if self.detach_in_progress:
                self.on_detach_abort(dev, evt, queue)
                self.detach_in_progress = False
            else:
                self.detach_in_progress = True
                self.on_detach_init(dev, evt, queue)

        elif isinstance(evt, events.DetachErrorEvent):
            if evt.err_timeout():
                self.log.warn('detachment process: timed out')
                self.on_detach_abort(dev, evt, queue)
                self.detach_in_progress = False

            else:
                self.log.error('unhandled error event: {}'.format(evt))

        elif isinstance(evt, events.LatchStateChangeEvent):
            self.on_latch_state_change(dev, evt, queue)

        else:
            self.log.warning('unhandled event: {}'.format(evt))

    def on_detach_init(self, dev, evt, queue):
        if self.task_attach_scheduled:
            self.skip_next_abort = True
            cmd.latch_request(dev)      # abort unlatch by sending request again
            return

        self.log.debug("detachment process: initiating")
        self.task_detach_scheduled += 1
        queue.put_nowait(self.task_detach(dev, evt))

    def on_detach_abort(self, dev, evt, queue):
        if self.skip_next_abort:
            self.skip_next_abort = False
            return

        self.log.debug("detachment process: aborting")
        self.task_abort_scheduled += 1
        queue.put_nowait(self.task_detach_abort(dev, evt))

    def on_connect(self, dev, evt, queue):
        self.log.debug("base connected")
        self.task_attach_scheduled += 1
        queue.put_nowait(self.task_attach(dev, evt))

    def on_disconnect(self, dev, evt, queue):
        self.log.debug("base disconnected")

        if self.notif is not None:
            self.notif.close()
            self.notif = None

    def on_op_mode_change(self, dev, evt, queue):
        self.log.debug("device mode changed to '{}'".format(cmd.opmode_str(evt.mode())))

    def on_latch_state_change(self, dev, evt, queue):
        if evt.latch_opened():
            notif = notify.SystemNotification('Surface DTX')
            notif.summary = 'Surface DTX'
            notif.body = 'Clipboard can be detached.'
            notif.hints['image-path'] = 'input-tablet'
            notif.hints['category'] = 'device'
            notif.hints['urgency'] = 2
            notif.hints['resident'] = True
            notif.timeout = 0

            self.notif = notif.show()

    async def task_detach(self, dev, evt):
        self.log.debug("task: detach start")

        if self.cfg.handler_detach:
            env = dict(os.environ)
            env["EXIT_DETACH_COMMENCE"] = str(PROC_EXIT_DETACH_COMMENCE)
            env["EXIT_DETACH_ABORT"] = str(PROC_EXIT_DETACH_ABORT)

            ret = await _run_handler(self.log, self.cfg.handler_detach, self.cfg, env=env)

            if not self.task_abort_scheduled:
                if ret == PROC_EXIT_DETACH_COMMENCE:
                    cmd.latch_open(dev)
                else:
                    cmd.latch_request(dev)      # abort unlatch by sending request again

        elif not self.task_abort_scheduled:
            cmd.latch_open(dev)

        self.task_detach_scheduled -= 1
        self.log.debug("task: detach done")

    async def task_detach_abort(self, dev, evt):
        self.log.debug("task: detach abort start")

        if self.cfg.handler_detach_abort:
            await _run_handler(self.log, self.cfg.handler_detach_abort, self.cfg)

        self.task_abort_scheduled -= 1
        self.log.debug("task: detach abort done")

    async def task_attach(self, dev, evt):
        self.log.debug("task: attach start")
        await asyncio.sleep(self.cfg.delay_attach)  # delay here to block other tasks

        if self.cfg.handler_attach:
            await _run_handler(self.log, self.cfg.handler_attach, self.cfg)

        self.task_attach_scheduled -= 1
        self.log.debug("task: attach done")

        notif = notify.SystemNotification('Surface DTX')
        notif.summary = 'Surface DTX'
        notif.body = 'Clipboard attached.'
        notif.hints['image-path'] = 'input-tablet'
        notif.hints['category'] = 'device'
        notif.hints['transient'] = True

        notif.show()


class TaskQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.active = True

    def put_nowait(self, task):
        self.queue.put_nowait(task)

    def empty(self):
        self.queue.empty()

    async def run(self):
        while not self.queue.empty() or self.active:
            task = await self.queue.get()
            await task
            self.queue.task_done()

    def soft_stop(self):
        self.active = False
        self.queue.put_nowait(self._noop())

    async def _noop(self):
        pass


def shutdown(dev, loop, queue):
    logging.info("Shutting down...")

    loop.remove_reader(dev.fd)
    loop.remove_signal_handler(signal.SIGTERM)
    loop.remove_signal_handler(signal.SIGINT)

    queue.soft_stop()


def run(cfg):
    logging.basicConfig(level=cfg.log.level, format=cfg.log.format, datefmt=cfg.log.datemft)
    handler = EventHandler(cfg)
    queue = TaskQueue()

    with Device.open() as dev:
        loop = asyncio.get_event_loop()
        try:
            loop.add_reader(dev.fd, _handle_read, dev, handler, queue)
            loop.add_signal_handler(signal.SIGTERM, shutdown, dev, loop, queue)
            loop.add_signal_handler(signal.SIGINT, shutdown, dev, loop, queue)
            loop.run_until_complete(queue.run())
        finally:
            loop.close()


def run_app():
    parser = argparse.ArgumentParser(
        prog="surface-dtx-daemon",
        description="Surface Detachment System (DTX) Daemon.")

    parser.add_argument(
        "-c", "--config",
        default=config.Config.DEFAULT_PATH,
        metavar="CFG",
        help="the configuration file to use")

    args = parser.parse_args()

    run(config.Config.load(args.config))
