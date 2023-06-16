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

from datetime import date, datetime, timedelta

import pytest

from hades.time.day_steps import datetime_to_step, days_in_year, quarter_from_datetime, step_to_date, step_to_datetime

EPOCH = datetime(1, 1, 1)


@pytest.mark.parametrize(
    "dt, expected_step",
    [
        (datetime(2023, 6, 9), (datetime(2023, 6, 9) - EPOCH).days),
        (date(2023, 6, 9), (datetime(2023, 6, 9) - EPOCH).days),
    ],
)
def test_datetime_to_step(dt, expected_step):
    assert datetime_to_step(dt) == expected_step


@pytest.mark.parametrize("step, expected_datetime", [(300, EPOCH + timedelta(days=300))])
def test_step_to_datetime(step, expected_datetime):
    assert step_to_datetime(step) == expected_datetime


@pytest.mark.parametrize("step, expected_date", [(300, (EPOCH + timedelta(days=300)).date())])
def test_step_to_date(step, expected_date):
    assert step_to_date(step) == expected_date


@pytest.mark.parametrize(
    "dt, expected_quarter",
    [
        (datetime(2023, 1, 1), 1),
        (datetime(2023, 4, 1), 2),
        (datetime(2023, 7, 1), 3),
        (datetime(2023, 10, 1), 4),
        (date(2023, 12, 31), 4),
    ],
)
def test_quarter_from_datetime(dt, expected_quarter):
    assert quarter_from_datetime(dt) == expected_quarter


@pytest.mark.parametrize(
    "dt, expected_days",
    [
        (datetime(2023, 1, 1), 365),  # Not a leap year
        (datetime(2024, 1, 1), 366),  # Leap year
        (date(2020, 12, 31), 366),  # Leap year
    ],
)
def test_days_in_year(dt, expected_days):
    assert days_in_year(dt) == expected_days
