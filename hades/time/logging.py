import logging
import sys

from hades.time.day_steps import step_to_date


class HadesEventFilter(logging.Filter):
    """prepend logs with the world date"""

    def __init__(self, world) -> None:
        super().__init__()
        self.world = world

    def filter(self, record):
        record.world_date = step_to_date(self.world.t)
        return True


formatter = logging.Formatter("%(levelname)-8s %(name)s:%(lineno)-4d [%(world_date)s] %(message)s")
syslog = logging.StreamHandler(stream=sys.stdout)
syslog.setFormatter(formatter)
