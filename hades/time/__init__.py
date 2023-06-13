"""
Time steps in hades can represent anything. This package contains some helper functions for common use cases particularly with time steps as days
"""

from hades.time.day_steps import datetime_to_step, days_in_year, quarter_from_datetime, step_to_date, step_to_datetime
from hades.time.event import QuarterStarted, YearStarted
from hades.time.process import QuarterStartScheduler, YearStartScheduler

__all__ = [
    "step_to_date",
    "datetime_to_step",
    "step_to_datetime",
    "days_in_year",
    "quarter_from_datetime",
    "YearStarted",
    "YearStartScheduler",
    "QuarterStarted",
    "QuarterStartScheduler",
]
