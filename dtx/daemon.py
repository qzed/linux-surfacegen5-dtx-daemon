from . import dtx
from . import notify
from . import commands as cmd
from . import config as cfg

import asyncio
import signal
import logging


def _get_op_mode_str(dev):
    opmode = cmd.get_op_mode(dev)

    if opmode == cmd.OP_MODE_LAPTOP:
        return "Laptop"

    if opmode == cmd.OP_MODE_TABLET:
        return "Tablet"

    if opmode == cmd.OP_MODE_SLATE:
        return "Slate"

    return "<unknown>"


async def _delayed(t, fn, *args):
    await asyncio.sleep(t)
    fn(*args)


def _handle_read(dev, handler):
    for evt in dev.read():
        handler(dev, evt)


class EventHandler:
    def __init__(self):
        self.in_progress = False
        self.notif = None
        self.log = logging.getLogger("handler")

    def __call__(self, dev, evt):
        if isinstance(evt, dtx.ConnectionChangeEvent):
            if evt.state():
                asyncio.create_task(_delayed(cfg.CONNECT_DELAY, self.on_connect_delayed, dev, evt))
                self.on_connect(dev, evt)
            else:
                self.in_progress = False
                self.on_disconnect(dev, evt)

        elif isinstance(evt, dtx.DetachButtonEvent):
            if self.in_progress:
                self.on_detach_abort(dev, evt)
                self.in_progress = False
            else:
                self.in_progress = True
                self.on_detach_initiate(dev, evt)

        elif isinstance(evt, dtx.DetachTimeoutEvent):
            self.on_detach_abort(dev, evt)
            self.in_progress = False

        elif isinstance(evt, dtx.DetachNotificationEvent):
            self.on_notify(dev, evt)

        else:
            self.log.warning('unhandled event: {}'.format(evt))

    def on_detach_initiate(self, dev, evt):
        self.log.debug("detachment process: initiating")
        cmd.detach_commence(dev)

    def on_detach_abort(self, dev, evt):
        self.log.debug("detachment process: aborting")

    def on_connect(self, dev, evt):
        self.log.debug("base connected")

    def on_connect_delayed(self, dev, evt):
        self.log.debug("device mode changed to '{}'".format(_get_op_mode_str(dev)))

    def on_disconnect(self, dev, evt):
        self.log.debug("base disconnected")
        self.log.debug("device mode changed to '{}'".format(_get_op_mode_str(dev)))

    def on_notify(self, dev, evt):
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


def run():
    logging.basicConfig(**cfg.LOG_CONFIG)

    handler = EventHandler()
    queue = asyncio.Queue()

    with dtx.Device.open() as dev:
        loop = asyncio.get_event_loop()
        try:
            loop.add_reader(dev.fd, _handle_read, dev, handler)
            loop.add_signal_handler(signal.SIGTERM, loop.stop)
            loop.add_signal_handler(signal.SIGINT, loop.stop)
            loop.run_forever()
        finally:
            logging.info("Shutting down...")

            loop.remove_reader(dev.fd)

            for task in asyncio.all_tasks(loop):
                task.cancel()

            loop.call_soon(loop.stop)
            loop.run_forever()
            loop.close()
