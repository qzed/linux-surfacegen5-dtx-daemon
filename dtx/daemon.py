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


async def _detach_init_async(dev, evt):
    logging.debug("detachment process: running init")
    await asyncio.sleep(5)
    logging.debug("detachment process: init done")
    cmd.detach_commence(dev)


async def _detach_abort_async(dev, evt):
    logging.debug("detachment process: running abort")
    await asyncio.sleep(5)
    logging.debug("detachment process: abort done")


class EventHandler:
    def __init__(self):
        self.in_progress = False
        self.notif = None
        self.log = logging.getLogger("handler")

    def __call__(self, dev, evt, queue):
        if isinstance(evt, dtx.ConnectionChangeEvent):
            if evt.state():
                conn_delayed = _delayed(cfg.CONNECT_DELAY, self.on_connect_delayed, dev, evt, queue)
                asyncio.create_task(conn_delayed)
                self.on_connect(dev, evt)
            else:
                self.in_progress = False
                self.on_disconnect(dev, evt, queue)

        elif isinstance(evt, dtx.DetachButtonEvent):
            if self.in_progress:
                self.on_detach_abort(dev, evt, queue)
                self.in_progress = False
            else:
                self.in_progress = True
                self.on_detach_initiate(dev, evt, queue)

        elif isinstance(evt, dtx.DetachTimeoutEvent):
            self.on_detach_abort(dev, evt, queue)
            self.in_progress = False

        elif isinstance(evt, dtx.DetachNotificationEvent):
            self.on_notify(dev, evt, queue)

        else:
            self.log.warning('unhandled event: {}'.format(evt))

    def on_detach_initiate(self, dev, evt, queue):
        self.log.debug("detachment process: initiating")
        queue.put_nowait(_detach_init_async(dev, evt))

    def on_detach_abort(self, dev, evt, queue):
        self.log.debug("detachment process: aborting")
        queue.put_nowait(_detach_abort_async(dev, evt))

    def on_connect(self, dev, evt, queue):
        self.log.debug("base connected")

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
