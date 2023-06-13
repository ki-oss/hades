import logging
from typing import Protocol, Type

from hades.core.hades import Hades


class HadesFilter(logging.Filter):
    def __init__(self, hades: Hades) -> None:
        self._hades = hades
        super().__init__()

    def filter(self, record):
        setattr(record, "step", self._hades.t)
        return True


def setup_step_logging(
    hades: Hades,
    fmt: str = "%(levelname)-8s %(name)s:%(lineno)-4d [t=%(step)d] %(message)s",
    filter_cls: Type[HadesFilter] = HadesFilter,
):
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(filter_cls(hades))
        handler.setFormatter(logging.Formatter(fmt))
