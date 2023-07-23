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

import time

import pytest
from pydantic import ConfigDict

from hades import Event


class GreekGodSpawned(Event):
    god_name: str
    address: tuple[str, str, str]
    powers: tuple[str, ...]


class GreekGodSpawnedDictStr(GreekGodSpawned):
    def __hash__(self) -> int:
        return hash(str(self.model_dump()))

    model_config = ConfigDict(frozen=False, mutable=False)


class GreekGodSpawnedFrozenSet(GreekGodSpawned):
    def __hash__(self) -> int:
        return hash(frozenset(self.model_dump().items()))

    model_config = ConfigDict(frozen=False, mutable=False)


class GreekGodSpawnedJson(GreekGodSpawned):
    def __hash__(self) -> int:
        return hash(self.model_dump_json())

    model_config = ConfigDict(frozen=False, mutable=False)


class GreekGodSpawnedRecursiveHash(GreekGodSpawned):
    def __hash__(self) -> int:
        return hash(tuple(hash(getattr(self, key)) for key in self.model_dump().keys()))

    model_config = ConfigDict(frozen=False, mutable=False)


@pytest.mark.performance
@pytest.mark.parametrize(
    "alternative", (GreekGodSpawnedFrozenSet, GreekGodSpawnedJson, GreekGodSpawnedRecursiveHash, GreekGodSpawnedDictStr)
)
def test_event_hashing_performance(alternative):
    total_time_actual = 0
    total_time_alternative = 0
    for _ in range(10_000):
        start_actual = time.time()
        hash(
            GreekGodSpawned(
                t=0, god_name="Zeus", address=("105", "Mount Olympus", "Greece"), powers=("lightning", "prom")
            )
        )
        end_actual = time.time()

        start_alternative = time.time()
        hash(
            alternative(t=0, god_name="Zeus", address=("105", "Mount Olympus", "Greece"), powers=("lightning", "prom"))
        )
        end_alternative = time.time()
        total_time_actual += end_actual - start_actual
        total_time_alternative += end_alternative - start_alternative

    assert (
        total_time_actual < total_time_alternative
    ), f"alternative {alternative} gave {total_time_alternative}! better than {total_time_actual}"
