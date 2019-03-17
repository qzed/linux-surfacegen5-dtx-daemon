from . import dtx
from . import notify
from . import commands as cmd
from . import config as cfg

import asyncio
import signal
import logging


async def _delayed(t, fn, *args):
    await asyncio.sleep(t)
    fn(*args)


def _handle_read(dev, handler, queue):
    for evt in dev.read():
        handler(dev, evt, queue)


class EventHandler:
    def __init__(self):
        self.log = logging.getLogger("handler")
        self.detach_in_progress = False
        self.task_detach_scheduled = 0
        self.task_abort_scheduled = 0
        self.task_attach_scheduled = 0
        self.skip_next_abort = False
        self.notif = None

    def __call__(self, dev, evt, queue):
        if isinstance(evt, dtx.ConnectionChangeEvent):
            if evt.state():
                conn_delayed = _delayed(cfg.DELAY_CONNECT, self.on_connect_delayed, dev, evt, queue)
                asyncio.create_task(conn_delayed)
                self.on_connect(dev, evt, queue)
            else:
                self.detach_in_progress = False
                self.on_disconnect(dev, evt, queue)

        elif isinstance(evt, dtx.DetachButtonEvent):
            if self.detach_in_progress:
                self.on_detach_abort(dev, evt, queue)
                self.detach_in_progress = False
            else:
                self.detach_in_progress = True
                self.on_detach_init(dev, evt, queue)

        elif isinstance(evt, dtx.DetachTimeoutEvent):
            self.on_detach_abort(dev, evt, queue)
            self.detach_in_progress = False

        elif isinstance(evt, dtx.DetachNotificationEvent):
            self.on_notify(dev, evt, queue)

        else:
            self.log.warning('unhandled event: {}'.format(evt))

    def on_detach_init(self, dev, evt, queue):
        if self.task_attach_scheduled:
            self.skip_next_abort = True
            cmd.detach_abort(dev)
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

    def on_connect_delayed(self, dev, evt, queue):
        self.log.debug("device mode changed to '{}'".format(cmd.op_mode_str(cmd.get_op_mode(dev))))

    def on_disconnect(self, dev, evt, queue):
        self.log.debug("base disconnected")
        self.log.debug("device mode changed to '{}'".format(cmd.op_mode_str(cmd.get_op_mode(dev))))

    def on_notify(self, dev, evt, queue):
        if evt.show():
            notif = notify.SystemNotification('Surface DTX')
            notif.summary = 'Surface DTX'
            notif.body = 'Clipboard can be detached.'
            notif.hints['image-path'] = 'input-tablet'
            notif.hints['category'] = 'device'
            notif.hints['urgency'] = 2
            notif.hints['resident'] = True
            notif.timeout = 0

            self.notif = notif.show()

        elif self.notif is not None:
            self.notif.close()

    async def task_detach(self, dev, evt):
        self.log.debug("task: detach start")

        await asyncio.sleep(5)          # TODO: implement real process execution

        if not self.task_abort_scheduled:
            cmd.detach_commence(dev)    # TODO: select command based on return value of process

        self.task_detach_scheduled -= 1
        self.log.debug("task: detach done")

    async def task_detach_abort(self, dev, evt):
        self.log.debug("task: detach abort start")

        await asyncio.sleep(5)          # TODO: implement real process execution

        self.task_abort_scheduled -= 1
        self.log.debug("task: detach abort done")

    async def task_attach(self, dev, evt):
        self.log.debug("task: attach start")
        await asyncio.sleep(cfg.DELAY_ATTACH)   # delay here to block other tasks

        await asyncio.sleep(5)          # TODO: implement real process execution

        self.task_attach_scheduled -= 1
        self.log.debug("task: attach done")


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


def run():
    logging.basicConfig(**cfg.LOG_CONFIG)

    handler = EventHandler()
    queue = TaskQueue()

    with dtx.Device.open() as dev:
        loop = asyncio.get_event_loop()
        try:
            loop.add_reader(dev.fd, _handle_read, dev, handler, queue)
            loop.add_signal_handler(signal.SIGTERM, shutdown, dev, loop, queue)
            loop.add_signal_handler(signal.SIGINT, shutdown, dev, loop, queue)
            loop.run_until_complete(queue.run())
        finally:
            loop.close()


# TODO: error handling when detach task fails?
