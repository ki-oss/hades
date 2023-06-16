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
