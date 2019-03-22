import logging
import toml

from pathlib import Path


def _flatten_dict_tuples(d, base=()):
    for k, v in d.items():
        if isinstance(v, dict):
            yield from _flatten_dict_tuples(v, base=base + (k,))
        else:
            yield base + (k,), v


def _flatten_dict(d):
    return dict([(".".join(k), v) for k, v in _flatten_dict_tuples(d)])


class LogConfig:
    def __init__(self):
        self.level = "DEBUG"
        self.format = "%(name)-8s %(levelname)-8s %(message)s"
        self.datemft = "%Y-%m-%dT%H:%M:%S%z"


class Config:
    DEFAULT_PATH = "/etc/surface-dtx/surface-dtx.cfg"

    def __init__(self):
        self.path = Path(__file__).parent.parent / "etc"
        self.log = LogConfig()
        self.delay_connect = 5
        self.delay_attach = 5
        self.handler_detach = None
        self.handler_detach_abort = None
        self.handler_attach = None

    @staticmethod
    def load(path=DEFAULT_PATH):
        cfg = Config()
        cfg.path = Path(path).parent.resolve()

        data = _flatten_dict(toml.load(path))

        if "log.level" in data:
            cfg.log.level = str(data["log.level"])

        if "log.format" in data:
            cfg.log.format = str(data["log.format"])

        if "log.datefmt" in data:
            cfg.log.datefmt = str(data["log.datefmt"])

        if "handler.detach" in data:
            cfg.handler_detach = str(data["handler.detach"])

        if "handler.detach_abort" in data:
            cfg.handler_detach_abort = str(data["handler.detach_abort"])

        if "handler.attach" in data:
            cfg.handler_attach = str(data["handler.attach"])

        if "delay.attach" in data:
            cfg.delay_attach = float(data["delay.attach"])

        return cfg
