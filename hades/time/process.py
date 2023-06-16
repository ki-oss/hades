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

import logging
from datetime import date

from hades import Event, NotificationResponse, Process, SimulationStarted
from hades.time.day_steps import datetime_to_step, step_to_date
from hades.time.event import QuarterStarted, YearStarted

_logger = logging.getLogger(__name__)


class YearStartScheduler(Process):
    """adds year start events to be used by other processes for scheduling things which come with an annual cadence,
    has no dependencies in terms of other events apart from the built-in SimulationStarted"""

    def __init__(self, start_year: int, look_ahead_years: int = 100) -> None:
        self._look_ahead_years = look_ahead_years
        self._start_year = start_year
        self._latest_year_added: int | None = None
        super().__init__()

    async def notify(self, event: Event) -> NotificationResponse:
        match event:
            case SimulationStarted(t=t) as e:
                _logger.debug(
                    "adding look ahead YearStarted events between %d and %d due to %s",
                    self._start_year,
                    self._look_ahead_years + self._start_year,
                    repr(e),
                )
                for year in range(self._start_year, self._look_ahead_years + self._start_year):
                    self.add_event(YearStarted(t=datetime_to_step(date(year, 1, 1))))
                self._latest_year_added = self._look_ahead_years + self._start_year - 1
                return NotificationResponse.ACK
            case YearStarted():
                return NotificationResponse.ACK_BUT_IGNORED
            case QuarterStarted():
                return NotificationResponse.ACK_BUT_IGNORED
            case Event(t=t) as e:
                # ensure that we keep the look ahead window maintained given other events
                if (
                    self._latest_year_added is not None
                    and (current_year := step_to_date(t).year) > self._latest_year_added - self._look_ahead_years + 1
                ):
                    _logger.debug(
                        "adding look ahead YearStarted events between %d and %d due to %s",
                        self._latest_year_added + 1,
                        current_year + self._look_ahead_years,
                        repr(e),
                    )
                    for year in range(self._latest_year_added + 1, current_year + self._look_ahead_years):
                        self.add_event(YearStarted(t=datetime_to_step(date(year, 1, 1))))
                        self._latest_year_added = year

                    return NotificationResponse.ACK
                return NotificationResponse.ACK_BUT_IGNORED
        return NotificationResponse.NO_ACK


class QuarterStartScheduler(Process):
    """adds quarter start events to be used for things occurring with a quarterly cadence. Depends on the YearStarted event
    being broadcast to it"""

    async def notify(self, event: Event) -> NotificationResponse:
        match event:
            case YearStarted(t=t):
                for i in range(4):
                    self.add_event(QuarterStarted(t=datetime_to_step(date(step_to_date(t).year, (i * 3) + 1, 1))))
                return NotificationResponse.ACK
        return NotificationResponse.NO_ACK
