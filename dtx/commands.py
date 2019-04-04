from . import ioctl

import struct


CMD_LATCH_LOCK    = ioctl.IO(0x11, 0x01)
CMD_LATCH_UNLOCK  = ioctl.IO(0x11, 0x02)
CMD_LATCH_REQUEST = ioctl.IO(0x11, 0x03)
CMD_LATCH_OPEN    = ioctl.IO(0x11, 0x04)
CMD_GET_OPMODE    = ioctl.IOR(0x11, 0x05, 4)

OPMODE_TABLET = 0x00
OPMODE_LAPTOP = 0x01
OPMODE_STUDIO = 0x02


def opmode_str(mode):
    try:
        return ['Tablet', 'Laptop', 'Studio'][mode]
    except IndexError:
        return '<unknown>'


def latch_lock(dev):
    dev.ioctl(CMD_LATCH_LOCK)


def latch_unlock(dev):
    dev.ioctl(CMD_LATCH_UNLOCK)


def latch_request(dev):
    dev.ioctl(CMD_LATCH_REQUEST)


def latch_open(dev):
    dev.ioctl(CMD_LATCH_OPEN)


def get_op_mode(dev):
    return struct.unpack('i', dev.ioctl(CMD_GET_OPMODE, bytes(4)))[0]
