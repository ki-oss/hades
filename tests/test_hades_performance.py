import json
import pickle
import struct
import time

import pytest

from hades import Event


class GreekGodSpawned(Event):
    god_name: str
    address: tuple[str, str, str]
    powers: tuple[str, ...]


class GreekGodSpawnedDictStr(GreekGodSpawned):
    def __hash__(self) -> int:
        return hash(str(self.dict()))
    
    class Config:
        frozen = False
        mutable = False


class GreekGodSpawnedFrozenSet(GreekGodSpawned):
    def __hash__(self) -> int:
        return hash(frozenset(self.dict().items()))

    class Config:
        frozen = False
        mutable = False


class GreekGodSpawnedJson(GreekGodSpawned):
    def __hash__(self) -> int:
        return hash(self.json())
    
    class Config:
        frozen = False
        mutable = False

    
class GreekGodSpawnedRecursiveHash(GreekGodSpawned):
    def __hash__(self) -> int:
        return hash(tuple(hash(getattr(self, key)) for key in self.dict().keys()))
    
    class Config:
        frozen = False
        mutable = False

@pytest.mark.performance
@pytest.mark.parametrize("alternative", (GreekGodSpawnedFrozenSet,GreekGodSpawnedJson, GreekGodSpawnedRecursiveHash, GreekGodSpawnedDictStr))
def test_event_hashing_performance(alternative):
    total_time_actual = 0
    total_time_alternative = 0
    for _ in range(10_000):
        start_actual = time.time()
        hash(GreekGodSpawned(
            t=0,
            god_name="Zeus",
            address=("105", "Mount Olympus", "Greece"),
            powers=("lightning", "prom")
        ))
        end_actual = time.time()

        start_alternative = time.time()
        hash(alternative(
            t=0,
            god_name="Zeus",
            address=("105", "Mount Olympus", "Greece"),
            powers=("lightning", "prom")
        ))
        end_alternative = time.time()
        total_time_actual += end_actual - start_actual
        total_time_alternative += end_alternative - start_alternative

    assert total_time_actual < total_time_alternative, (
        f"alternative {alternative} gave {total_time_alternative}! better than"
        f" {total_time_actual}"
    )
