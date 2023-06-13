from datetime import datetime, timedelta

import pytest

from hades import Event, NotificationResponse, SimulationStarted
from hades.time import (
    QuarterStarted,
    QuarterStartScheduler,
    YearStarted,
    YearStartScheduler,
    datetime_to_step,
    step_to_date,
)


async def test_initializes_correctly():
    events_added = []
    # Initialize a YearStartScheduler with a starting year of 2023 and a look-ahead of 10 years
    scheduler = YearStartScheduler(start_year=2023, look_ahead_years=10)
    scheduler.add_event_to_hades = lambda _, e: events_added.append(e)

    # Simulate the start of the simulation
    await scheduler.notify(SimulationStarted(t=1))

    # Check that YearStarted events have been created for the next 10 years
    assert len(events_added) == 10
    assert all(isinstance(event, YearStarted) for event in events_added)

    # The last year added should be 2032
    assert scheduler._latest_year_added == 2032


@pytest.mark.parametrize("event", (YearStarted, QuarterStarted))
async def test_ignores_time_events_started(event):
    events_added = []
    scheduler = YearStartScheduler(start_year=2023, look_ahead_years=10)
    scheduler.add_event_to_hades = lambda _, e: events_added.append(e)
    await scheduler.notify(SimulationStarted(t=1))

    # ignores year started events
    await scheduler.notify(event(t=datetime_to_step(datetime(2023, 1, 1) + timedelta(days=365))))
    assert len(events_added) == 10  # no new events added


async def test_adds_year_on_new_event():
    events_added = []
    # Initialize a YearStartScheduler with a starting year of 2023 and a look-ahead of 10 years
    scheduler = YearStartScheduler(start_year=2023, look_ahead_years=10)
    scheduler.add_event_to_hades = lambda _, e: events_added.append(e)

    # Simulate the start of the simulation
    await scheduler.notify(SimulationStarted(t=1))

    # Simulate another event (which is not Simulation Started) a year later
    await scheduler.notify(Event(t=datetime_to_step(datetime(2023, 1, 1) + timedelta(days=365))))

    # Check that a new YearStarted event has been created
    assert len(events_added) == 11
    assert isinstance(events_added[-1], YearStarted)

    # The last year added should now be 2033
    assert scheduler._latest_year_added == 2033
    # by induction we should be good to go!


async def test_other_events_which_happen_during_the_window_are_ignored():
    events_added = []
    # Initialize a YearStartScheduler with a starting year of 2023 and a look-ahead of 10 years
    scheduler = YearStartScheduler(start_year=2023, look_ahead_years=10)
    scheduler.add_event_to_hades = lambda _, e: events_added.append(e)

    # Simulate the start of the simulation
    await scheduler.notify(SimulationStarted(t=1))

    # Simulate another event (which is not Simulation Started) a year later
    await scheduler.notify(Event(t=datetime_to_step(datetime(2023, 2, 1))))

    # Check that a no new YearStarted event has been created
    assert len(events_added) == 10


async def test_no_ack_for_non_events():
    scheduler = YearStartScheduler(start_year=2023, look_ahead_years=10)
    assert await scheduler.notify(None) == NotificationResponse.NO_ACK


async def test_all_events_happen_on_first_of_january():
    events_added = []
    # Initialize a YearStartScheduler with a starting year of 2023 and a look-ahead of 10 years
    scheduler = YearStartScheduler(start_year=2023, look_ahead_years=10)
    scheduler.add_event_to_hades = lambda _, e: events_added.append(e)

    # Simulate the start of the simulation
    await scheduler.notify(SimulationStarted(t=1))

    # Simulate another event (which is not Simulation Started) a and a  bit year later
    await scheduler.notify(Event(t=datetime_to_step(datetime(2023, 1, 1) + timedelta(days=400))))

    # Check that a new YearStarted event has been created
    assert all(step_to_date(event.t).day == 1 and step_to_date(event.t).month == 1 for event in events_added)


async def test_quarter_started_process_schedules_quarter_started_event_from_year_started_events():
    events_added = []
    scheduler = QuarterStartScheduler()
    scheduler.add_event_to_hades = lambda _, e: events_added.append(e)

    # Simulate the start of the year
    await scheduler.notify(YearStarted(t=datetime_to_step(datetime(2023, 1, 1))))

    assert events_added == [
        QuarterStarted(t=datetime_to_step(datetime(2023, 1, 1))),
        QuarterStarted(t=datetime_to_step(datetime(2023, 4, 1))),
        QuarterStarted(t=datetime_to_step(datetime(2023, 7, 1))),
        QuarterStarted(t=datetime_to_step(datetime(2023, 10, 1))),
    ]


async def test_quarter_started_process_no_acks_for_other_events():
    scheduler = QuarterStartScheduler()
    assert await scheduler.notify(Event(t=2)) == NotificationResponse.NO_ACK
