from . import dtx
from . import notify


class EventHandler:
    def __init__(self):
        self.in_progress = False
        self.notif = None

    def __call__(self, dev, evt):
        if isinstance(evt, dtx.ConnectionChangeEvent):
            self.in_progress = False
            self.on_connection_change(dev, evt)

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

    def on_connection_change(self, dev, evt):
        if evt.state():
            print("DEBUG: base connected")
        else:
            print("DEBUG: base disconnected")

    def on_detach_initiate(self, dev, evt):
        print("DEBUG: detachment process: initiating")
        dev.write(dtx.Command.BaseDetachCommence)

    def on_detach_abort(self, dev, evt):
        print("DEBUG: detachment process: aborting")

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

    with dtx.Device.open() as dev:
        for evt in dev.read_loop():
            handler(dev, evt)
