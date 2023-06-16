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

from datetime import datetime

from hades.time import QuarterStarted, YearStarted, datetime_to_step


def test_year_started():
    event = YearStarted(t=datetime_to_step(datetime(2023, 1, 1)))
    assert event.year == 2023
    assert event.is_leap == False
    assert event.number_of_days == 365

    leap_event = YearStarted(t=datetime_to_step(datetime(2024, 1, 1)))
    assert leap_event.year == 2024
    assert leap_event.is_leap == True
    assert leap_event.number_of_days == 366


def test_quarter_started():
    first_quarter_event = QuarterStarted(t=datetime_to_step(datetime(2023, 1, 1)))
    assert first_quarter_event.year == 2023
    assert first_quarter_event.quarter_number == 1

    second_quarter_event = QuarterStarted(t=datetime_to_step(datetime(2023, 4, 1)))
    assert second_quarter_event.year == 2023
    assert second_quarter_event.quarter_number == 2

    third_quarter_event = QuarterStarted(t=datetime_to_step(datetime(2023, 7, 1)))
    assert third_quarter_event.year == 2023
    assert third_quarter_event.quarter_number == 3

    fourth_quarter_event = QuarterStarted(t=datetime_to_step(datetime(2023, 10, 1)))
    assert fourth_quarter_event.year == 2023
    assert fourth_quarter_event.quarter_number == 4
