import os
import select
import subprocess
import struct
import fcntl


class Event:
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


class ConnectionChangeEvent(Event):
    def __init__(self, state, arg1):
        super().__init__(0x11, 0x0c, state, arg1)

    def __str__(self):
        return "ConnectionChangeEvent (state: {})" \
                .format("Connected" if self.state() else "Disconnected")

    def state(self):
        return self.arg0 == 0x01


class DetachButtonEvent(Event):
    def __init__(self):
        super().__init__(0x11, 0x0e)

    def __str__(self):
        return "DetachButtonEvent"


class DetachTimeoutEvent(Event):
    def __init__(self, arg0):
        super().__init__(0x11, 0x0f, arg0)

    def __str__(self):
        return "DetachTimeoutEvent (arg0: {})".format(self.arg0)


class DetachNotificationEvent(Event):
    def __init__(self, state):
        super().__init__(0x11, 0x11, state)

    def show(self):
        return self.arg0 == 0x01

    def __str__(self):
        return "DetachNotificationEvent (show: {})".format(self.show())


def _dtx_event_from_bytes(type, code, arg0, arg1):
    if type == 0x11 and code == 0x0c:
        return ConnectionChangeEvent(arg0, arg1)

    if type == 0x11 and code == 0x0e:
        return DetachButtonEvent()

    if type == 0x11 and code == 0x0f:
        return DetachTimeoutEvent(arg0)

    if type == 0x11 and code == 0x11:
        return DetachNotificationEvent(arg0)

    return Event(type, code, arg0, arg1)


class Device:
    _NATIVE_EVENT_BUF_SIZE = 16 * 4

    @staticmethod
    def open(path='/dev/surface_dtx', oflags=os.O_RDWR | os.O_NONBLOCK):
        fd = os.open(path, oflags)

        return Device(fd)

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
        data = os.read(self.fd, Device._NATIVE_EVENT_BUF_SIZE)

        for event in struct.iter_unpack('BBBB', data):
            yield _dtx_event_from_bytes(*event)

    def read_loop(self):
        while True:
            select.select([self.fd], [], [])
            for event in self.read():
                yield event

    def ioctl(self, request, arg=0):
        return fcntl.ioctl(self.fd, request, arg)
