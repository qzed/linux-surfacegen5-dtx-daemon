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
    def __init__(self, type, code):
        self.type = type
        self.code = code

    def __eq__(self, other):
        return self.type == other.type and self.code == other.code


DtxEvent.BaseDetachRequest = DtxEvent(0x11, 0x0e)


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

        for event in struct.iter_unpack('BB', data):
            yield DtxEvent(*event)

    def read_loop(self):
        while True:
            select.select([self.fd], [], [])
            for event in self.read():
                yield event

    def write(self, cmd):
        os.write(self.fd, bytes([cmd.type, cmd.code]))


def handle_detach_event(dev, evt):
    dev.write(DtxCommand.BaseDetachCommence)    # TODO


def handle_event(dev, evt):
    if evt == DtxEvent.BaseDetachRequest:
        handle_detach_event(dev, evt)
    else:
        print('WARNING: unknown request: 0x{:02x}'.format(evt.code))


def main():
    with DtxDevice.open() as dev:
        for evt in dev.read_loop():
            handle_event(dev, evt)


if __name__ == '__main__':
    main()
