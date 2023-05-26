import calendar

from hades import Event
from hades.time.day_steps import quarter_from_datetime, step_to_date


class YearStarted(Event):
    """the year started on this day (e.g. 1/1)"""

    @property
    def year(self) -> int:
        return step_to_date(self.t).year

    @property
    def is_leap(self) -> bool:
        return calendar.isleap(self.year)

    @property
    def number_of_days(self) -> int:
        return 365 + int(self.is_leap)


class QuarterStarted(Event):
    """the quarter started on this day"""

    @property
    def year(self) -> int:
        return step_to_date(self.t).year

    @property
    def quarter_number(self) -> int:
        return quarter_from_datetime(step_to_date(self.t))
