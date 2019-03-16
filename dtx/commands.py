from . import ioctl

import struct


CMD_SAFEGUARD_ENGAGE    = ioctl.IO(0x11, 0x01)
CMD_SAFEGUARD_DISENGAGE = ioctl.IO(0x11, 0x02)
CMD_DETACH_ABORT        = ioctl.IO(0x11, 0x03)
CMD_DETACH_COMMENCE     = ioctl.IO(0x11, 0x04)
CMD_GET_OP_MODE         = ioctl.IOR(0x11, 0x05, 4)

OP_MODE_TABLET = 0x00
OP_MODE_LAPTOP = 0x01
OP_MODE_SLATE  = 0x02


def safeguard_engage(dev):
    dev.ioctl(CMD_SAFEGUARD_ENGAGE)


def safeguard_disengage(dev):
    dev.ioctl(CMD_SAFEGUARD_DISENGAGE)


def detach_abort(dev):
    dev.ioctl(CMD_DETACH_ABORT)


def detach_commence(dev):
    dev.ioctl(CMD_DETACH_COMMENCE)


def get_op_mode(dev):
    return struct.unpack('i', dev.ioctl(CMD_GET_OP_MODE, bytes(4)))[0]
