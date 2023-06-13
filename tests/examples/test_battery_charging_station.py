import pytest
from examples.battery_charging_station import bcs


@pytest.mark.example
async def test_battery_charging_station_gives_correct_output(capsys):
    await bcs()
    assert capsys.readouterr().out == """Car 0 arriving at 0
Car 0 starting to charge at 0
Car 1 arriving at 2
Car 1 starting to charge at 2
Car 2 arriving at 4
Car 0 leaving the bcs at 5
Car 2 starting to charge at 5
Car 3 arriving at 6
Car 1 leaving the bcs at 7
Car 3 starting to charge at 7
Car 2 leaving the bcs at 10
Car 3 leaving the bcs at 12
"""
