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
