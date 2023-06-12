import logging

from hades.core.hades import Hades
from hades.logging import HadesFilter, setup_step_logging
from hades.time.day_steps import step_to_date


class HadesDateFilter(HadesFilter):
    def filter(self, record):
        setattr(record, "world_date", step_to_date(self._hades.t))
        return super().filter(record)


def setup_date_logging(
    hades: Hades,
    fmt: str = "%(levelname)-8s %(name)s:%(lineno)-4d [%(world_date)s] %(message)s",
):
    setup_step_logging(hades, fmt, HadesDateFilter)
