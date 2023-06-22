# Copyright 2023 Brit Group Services Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import calendar
from datetime import date, datetime, timedelta
from typing import Union

EPOCH = datetime(1, 1, 1)


def datetime_to_step(dt: Union[datetime, date], epoch: datetime = EPOCH) -> int:
    """datetime or date as days since epoch"""
    if not isinstance(dt, datetime):
        return datetime_to_step(datetime.fromisoformat(dt.isoformat()))
    return int((dt - epoch).total_seconds() // timedelta(days=1).total_seconds())


def step_to_datetime(step: int, epoch: datetime = EPOCH) -> datetime:
    """days since epoch as datetime"""
    return epoch + timedelta(days=step)


def step_to_date(step: int) -> date:
    """days since epoch as date"""
    return step_to_datetime(step).date()


def quarter_from_datetime(dt: Union[datetime, date]) -> int:
    return ((dt.month - 1) // 3) + 1


def days_in_year(dt: Union[datetime, date]) -> int:
    return 365 + int(calendar.isleap(dt.year))
