#!/usr/bin/env python3

# TODO:  check if handling already in progress / detached

import os
import select
import subprocess
import struct


class DtxCommand:
    def __init__(self, type, code):
        self.type = type
        self.code = code

    def __eq__(self, other):
        return self.type == other.type and self.code == other.code


DtxCommand.BaseDetachAbort = DtxCommand(0x11, 0x08)
DtxCommand.BaseDetachCommence = DtxCommand(0x11, 0x09)


class DtxEvent:
    def __init__(self, type, code, arg0=0x00, arg1=0x00):
        self.type = type
        self.code = code
        self.arg0 = arg0
        self.arg1 = arg1

    def __eq__(self, other):
        return self.type == other.type and self.code == other.code

    def __repr__(self):
        return "DtxEvent (type: 0x{:02x}, code: 0x{:02x}, arg0: 0x{:02x}, arg1: 0x{:02x})" \
                .format(self.type, self.code, self.arg0, self.arg1)


class ConnectionChangeEvent(DtxEvent):
    def __init__(self, state, arg1):
        super().__init__(0x11, 0x0c, state, arg1)

    def __str__(self):
        return "ConnectionChangeEvent (state: {})" \
                .format("Connected" if self.state() else "Disconnected")

    def state(self):
        return self.arg0 == 0x01


class DetachButtonEvent(DtxEvent):
    def __init__(self):
        super().__init__(0x11, 0x0e)

    def __str__(self):
        return "DetachButtonEvent"


class DetachTimeoutEvent(DtxEvent):
    def __init__(self, arg0):
        super().__init__(0x11, 0x0f, arg0)

    def __str__(self):
        return "DetachTimeoutEvent (arg0: {})".format(self.arg0)


class DetachNotificationEvent(DtxEvent):
    def __init__(self, state):
        super().__init__(0x11, 0x11, state)

    def state(self):
        return self.arg0 == 0x01

    def __str__(self):
        return "DetachNotificationEvent (state: {})" \
                .format("On" if self.state() else "Off")


def _dtx_event_from_bytes(type, code, arg0, arg1):
    if type == 0x11 and code == 0x0c:
        return ConnectionChangeEvent(arg0, arg1)

    if type == 0x11 and code == 0x0e:
        return DetachButtonEvent()

    if type == 0x11 and code == 0x0f:
        return DetachTimeoutEvent(arg0)

    if type == 0x11 and code == 0x11:
        return DetachNotificationEvent(arg0)

    return DtxEvent(type, code, arg0, arg1)


class DtxDevice:
    _NATIVE_EVENT_BUF_SIZE = 16 * 2

    @staticmethod
    def open(path='/dev/surface_dtx', oflags=os.O_RDWR | os.O_NONBLOCK):
        fd = os.open(path, oflags)

        return DtxDevice(fd)

    def __init__(self, fd):
        self.fd = fd

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self.close()

    def close(self):
        if self.fd is not None:
            os.close(self.fd)

    def read(self):
        data = os.read(self.fd, DtxDevice._NATIVE_EVENT_BUF_SIZE)

        for event in struct.iter_unpack('BBBB', data):
            yield _dtx_event_from_bytes(*event)

    def read_loop(self):
        while True:
            select.select([self.fd], [], [])
            for event in self.read():
                yield event

    def write(self, cmd):
        os.write(self.fd, bytes([cmd.type, cmd.code]))


class EventHandler:
    def __call__(self, dev, evt):
        print("received event: {}".format(repr(evt)))

        if isinstance(evt, ConnectionChangeEvent):
            pass    # TODO

        elif isinstance(evt, DetachButtonEvent):
            dev.write(DtxCommand.BaseDetachCommence)    # TODO

        elif isinstance(evt, DetachTimeoutEvent):
            pass    # TODO

        elif isinstance(evt, DetachNotificationEvent):
            pass    # TODO

        else:
            print('WARNING: unhandled event: {}'.format(evt))


def main():
    handler = EventHandler()

    with DtxDevice.open() as dev:
        for evt in dev.read_loop():
            handler(dev, evt)


if __name__ == '__main__':
    main()
