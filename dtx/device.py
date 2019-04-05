from . import commands
from . import events

import fcntl
import os
import struct


def _dtx_event_from_bytes(type, code, arg0, arg1):
    if type == 0x11 and code == 0x0c:
        return events.ConnectionChangeEvent(arg0, arg1)

    if type == 0x11 and code == 0x0d:
        return events.OpModeChangeEvent(arg0)

    if type == 0x11 and code == 0x0e:
        return events.DetachButtonEvent()

    if type == 0x11 and code == 0x0f:
        return events.DetachErrorEvent(arg0)

    if type == 0x11 and code == 0x11:
        return events.LatchStateChangeEvent(arg0)

    return events.Event(type, code, arg0, arg1)


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

    def ioctl(self, request, arg=0):
        return fcntl.ioctl(self.fd, request, arg)
