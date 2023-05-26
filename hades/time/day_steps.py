import calendar
from datetime import date, datetime, timedelta
from typing import Union

EPOCH = datetime(1, 1, 1)


def datetime_to_step(dt: Union[datetime, date]) -> int:
    """datetime or date as days since epoch"""
    if not isinstance(dt, datetime):
        return datetime_to_step(datetime.fromisoformat(dt.isoformat()))
    return int((dt - EPOCH).total_seconds() // timedelta(days=1).total_seconds())


def step_to_datetime(step: int) -> datetime:
    """days since epoch as datetime"""
    return EPOCH + timedelta(days=step)


def step_to_date(step: int) -> date:
    """days since epoch as date"""
    return step_to_datetime(step).date()


def quarter_from_datetime(dt: Union[datetime, date]) -> int:
    return ((dt.month - 1) // 3) + 1


def days_in_year(dt: Union[datetime, date]) -> int:
    return 365 + int(calendar.isleap(dt.year))
