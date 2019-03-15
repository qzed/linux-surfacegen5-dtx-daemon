#!/usr/bin/env python3
import dtx
import notify


class EventHandler:
    def __init__(self):
        self.notif = None

    def __call__(self, dev, evt):
        print("received event: {}".format(evt))

        if isinstance(evt, dtx.ConnectionChangeEvent):
            self.event_connection_change(dev, evt)

        elif isinstance(evt, dtx.DetachButtonEvent):
            self.event_detach_button(dev, evt)

        elif isinstance(evt, dtx.DetachTimeoutEvent):
            self.event_detach_timeout(dev, evt)

        elif isinstance(evt, dtx.DetachNotificationEvent):
            self.event_notify(dev, evt)

        else:
            print('WARNING: unhandled event: {}'.format(evt))

    def event_connection_change(self, dev, evt):
        pass

    def event_detach_button(self, dev, evt):
        dev.write(dtx.Command.BaseDetachCommence)

    def event_detach_timeout(self, dev, evt):
        pass

    def event_notify(self, dev, evt):
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


def main():
    handler = EventHandler()

    with dtx.Device.open() as dev:
        for evt in dev.read_loop():
            handler(dev, evt)


if __name__ == '__main__':
    main()
