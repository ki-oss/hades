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

import asyncio

from hades import Event, Hades, NotificationResponse, Process


class EventOne(Event):
    pass


class EventTwo(Event):
    pass


class MyProcess(Process):
    def __init__(self):
        super().__init__()
        self._event_data_list = []

    async def notify(self, event: Event):
        match event:
            case EventOne(t=t):
                print("event one arrives first")
                await asyncio.sleep(0.1)  # Simulate a delay
                self._event_data_list.append("One")
                return NotificationResponse.ACK
            case EventTwo(t=t):
                print("event two arrives second")
                await asyncio.sleep(0.05)
                self._event_data_list.append("Two")
                return NotificationResponse.ACK
        return NotificationResponse.NO_ACK


class MyLockingProcess(MyProcess):
    def __init__(self):
        super().__init__()
        self.lock = asyncio.Lock()

    async def notify(self, event: Event):
        async with self.lock:
            return await super().notify(event)


async def test_async_notify(capsys):
    hades = Hades()

    process = MyProcess()

    hades.register_process(process)

    # note these arrive at the same timestep
    hades.add_event(process, EventOne(t=0))
    hades.add_event(process, EventTwo(t=0))

    await hades.run()

    # two happens before one
    assert process._event_data_list == ["Two", "One"]
    # even though one arrives before two
    assert capsys.readouterr().out == """event one arrives first
event two arrives second
"""


async def test_async_notify_with_lock(capsys):
    hades = Hades()

    process = MyLockingProcess()

    hades.register_process(process)

    hades.add_event(process, EventOne(t=0))
    hades.add_event(process, EventTwo(t=0))

    await hades.run()

    # with the lock events happen in the order they arrive.
    assert process._event_data_list == ["One", "Two"]
    assert capsys.readouterr().out == """event one arrives first
event two arrives second
"""
