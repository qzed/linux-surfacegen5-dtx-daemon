from . import commands

import fcntl
import os
import struct


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


class OpModeChangeEvent(Event):
    def __init__(self, mode):
        super().__init__(0x11, 0x0c, mode)

    def __str__(self):
        return "OpModeChangeEvent (mode: {})" \
               .format(commands.opmode_str(self.mode()))

    def mode(self):
        return self.arg0


class DetachButtonEvent(Event):
    def __init__(self):
        super().__init__(0x11, 0x0e)

    def __str__(self):
        return "DetachButtonEvent"


class DetachErrorEvent(Event):
    def __init__(self, errnum):
        super().__init__(0x11, 0x0f, errnum)

    def __str__(self):
        return "DetachErrorEvent (code: {})".format(self.arg0)

    def errnum(self):
        return self.arg0

    def err_timeout(self):
        return self.errnum() == 0x02

    # other currently unknown codes are (obtained from driver strings)
    # - SSH_LATCHES_STATE_FAILED_TO_UNLOCK
    # - SSH_LATCHES_STATE_FAILED_TO_REMAIN_UNLOCKED
    # - SSH_LATCHES_STATE_FAILED_TO_RELOCK


class LatchStateChangeEvent(Event):
    def __init__(self, state):
        super().__init__(0x11, 0x11, state)

    def __str__(self):
        return "LatchStateChangeEvent (show: {})".format(self.show())

    def latch_opened(self):
        return self.arg0 == 0x01

    def latch_closed(self):
        return self.arg0 == 0x00


def _dtx_event_from_bytes(type, code, arg0, arg1):
    if type == 0x11 and code == 0x0c:
        return ConnectionChangeEvent(arg0, arg1)

    if type == 0x11 and code == 0x0d:
        return OpModeChangeEvent(arg0)

    if type == 0x11 and code == 0x0e:
        return DetachButtonEvent()

    if type == 0x11 and code == 0x0f:
        return DetachErrorEvent(arg0)

    if type == 0x11 and code == 0x11:
        return LatchStateChangeEvent(arg0)

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

    def ioctl(self, request, arg=0):
        return fcntl.ioctl(self.fd, request, arg)
