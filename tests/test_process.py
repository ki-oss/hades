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

import pytest

from hades import Event, Hades, PredefinedEventAdder, Process, ProcessUnregistered, RandomProcess, SimulationStarted
from hades.core.process import NotificationResponse


def test_add_event_needs_add_event_to_hades_callback_set():
    with pytest.raises(ValueError):
        Process().add_event(Event(t=1))


async def test_if_notify_is_not_implemented_error_raised():
    with pytest.raises(NotImplementedError):
        await Process().notify(Event(t=1))


async def test_random_process_is_consistent_with_seed():
    process = RandomProcess(seed="pompom")
    assert process.random.randint(1, 100) == 74
    assert str(process._generate_uuid()) == "9fcade5e-45b8-4800-b51e-bbb7d13a66de"

    process_2 = RandomProcess(seed="pompom")
    assert process_2.random.randint(1, 100) == 74
    assert str(process_2._generate_uuid()) == "9fcade5e-45b8-4800-b51e-bbb7d13a66de"


async def test_predefined_event_adder_adds_events_to_hades():
    h = Hades()
    h.register_process(PredefinedEventAdder(predefined_events=[Event(t=2), Event(t=3)], name="adder boy"))
    await h.run()

    assert [e[0][0] for e in h.event_history] == [
        SimulationStarted(t=0),
        ProcessUnregistered(t=0),
        Event(t=2),
        Event(t=3),
    ]


async def test_predefined_event_adder_ignores_events_other_than_simulation_started():
    assert (
        await PredefinedEventAdder(predefined_events=[], name="blah").notify(Event(t=1)) == NotificationResponse.NO_ACK
    )
