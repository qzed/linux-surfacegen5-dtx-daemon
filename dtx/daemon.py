from . import dtx
from . import notify
from . import commands

import asyncio
import signal


def _get_op_mode_str(dev):
    opmode = commands.get_op_mode(dev)

    if opmode == commands.OP_MODE_LAPTOP:
        return "Laptop"

    if opmode == commands.OP_MODE_TABLET:
        return "Tablet"

    if opmode == commands.OP_MODE_SLATE:
        return "Slate"

    return "<unknown>"


async def _check_device_mode_delayed(dev):
    await asyncio.sleep(5)
    print("DBEUG: device mode changed to '{}'".format(_get_op_mode_str(dev)))


def _handle_read(dev, handler):
    for evt in dev.read():
        handler(dev, evt)


class EventHandler:
    def __init__(self):
        self.in_progress = False
        self.notif = None

    def __call__(self, dev, evt):
        if isinstance(evt, dtx.ConnectionChangeEvent):
            if evt.state():
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
            print('WARNING: unhandled event: {}'.format(evt))

    def on_detach_initiate(self, dev, evt):
        print("DEBUG: detachment process: initiating")
        commands.detach_commence(dev)

    def on_detach_abort(self, dev, evt):
        print("DEBUG: detachment process: aborting")

    def on_connect(self, dev, evt):
        print("DEBUG: base connected")
        asyncio.create_task(_check_device_mode_delayed(dev))

    def on_disconnect(self, dev, evt):
        print("DEBUG: base disconnected")
        print("DBEUG: device mode changed to '{}'".format(_get_op_mode_str(dev)))

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
            print("INFO: Shutting down...")

            for task in asyncio.all_tasks(loop):
                task.cancel()

            loop.call_soon(loop.stop)
            loop.run_forever()
            loop.close()
