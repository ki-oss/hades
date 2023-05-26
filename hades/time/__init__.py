"""
Time steps, in hades can represent anything. However here are some helper functions included for common use cases particularly with time steps as days
since most things within insurance dont need more resolution that this.
"""

from hades.time.day_steps import datetime_to_step, days_in_year, quarter_from_datetime, step_to_date
from hades.time.event import QuarterStarted, YearStarted
from hades.time.process import QuarterStartScheduler, YearStartScheduler

__all__ = [
    "step_to_date",
    "datetime_to_step",
    "days_in_year",
    "quarter_from_datetime",
    "YearStarted",
    "YearStartScheduler",
    "QuarterStarted",
    "QuarterStartScheduler",
]
