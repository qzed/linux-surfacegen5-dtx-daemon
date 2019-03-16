_IOC_NRBITS   = 8
_IOC_TYPEBITS = 8
_IOC_SIZEBITS = 14
_IOC_DIRBITS  = 2

_IOC_NRSHIFT  = 0
_IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
_IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
_IOC_DIRSHIFT  = _IOC_SIZESHIFT + _IOC_SIZEBITS

_IOC_NONE  = 0
_IOC_WRITE = 1
_IOC_READ  = 2


def _IOC(dir, type, nr, size):
    return (((dir) << _IOC_DIRSHIFT) |
            ((type) << _IOC_TYPESHIFT) |
            ((nr) << _IOC_NRSHIFT) |
            ((size) << _IOC_SIZESHIFT))


def IO(type, nr):
    return _IOC(_IOC_NONE, type, nr, 0)


def IOR(type, nr, size):
    return _IOC(_IOC_READ, type, nr, size)


def IOW(type, nr, size):
    return _IOC(_IOC_WRITE, type, nr, size)


def IOWR(type, nr, size):
    return _IOC(_IOC_WRITE | _IOC_READ, type, nr, size)
