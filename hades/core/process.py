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
The entity doing the main body of work within the simulation is the `Process`. The `notify(event)` method of every process registered 
(via `hades_instance.register_process()`) will be called for each event in the queue for the next time step as a group of asynchronous tasks.
That is to say: events are broadcast and handled asynchronously by the registered processes. 
For justification of this see the [design justification](../../design-justification).

## Pattern matching events

The pattern suggested for processes, is for the process to `match` events that it uses and respond with some sort of acknowledgement of what was done with the event. E.g.

```python
from hades import NotificationResponse, Hades, Event

class MyProcess(Process):
    def __init__(self, important_identifiers: list[str]):
        self._important_identifiers = important_identifiers

    async def notify(self event: Event):
        match event:
            case SomeEvent(t=t, some_identifier=some_identifier, data=data):
                if some_identifier not in important_identifiers:
                    return NotificationResponse.ACK_BUT_IGNORED
                data_for_other_event = self._do_something_with_data(d)
                self.add_event(OtherEvent(t=t+1, data=data_for_other_event))
                return NotificationResponse.ACK
        return NotificationResponse.NO_ACK
```

## Process Notifications and Asynchronous Handling

The Hades Framework's core functionality involves handling and broadcasting events asynchronously. 
The implementation uses Python's native asyncio library for task scheduling and execution. 
All events for a given time-step are broadcast to all registered processes and handled independently within their context.

## Asynchronous Behaviour and Data Consistency

However, as powerful as this design pattern may be, it also introduces a certain level of complexity when dealing with shared data resources.

Consider the scenario where multiple events are sent to a single process, and each event triggers modifications on a shared data resource, for example, a list within the process. Since all the events are handled asynchronously and independently, the order of execution is not guaranteed, and data inconsistency can arise due to race conditions.

This is a critical aspect of using the Hades Framework: always ensure data consistency and thread-safety when designing your processes.

### Managing Asynchronous Operations within Processes

Here are some recommended ways to handle shared data within processes:

* Use synchronization primitives: Python's asyncio library provides several synchronization primitives like locks (asyncio.Lock()) and semaphores (asyncio.Semaphore()). 
Use these primitives to ensure only one coroutine within a process modifies the shared resource at any given time.
* Immutable data structures: If possible, use immutable data structures. This eliminates the possibility of shared data being modified concurrently by different coroutines, thus avoiding race conditions.
* Avoid shared state: Whenever possible, avoid using shared state within processes. Design your processes such that they work primarily with local data (from the event).

!!! Note
    There is no need to worry about this between processes (as they shouldn't share mutable state), only multiple events handled within the same process.

Example of this:
```python
--8<-- "tests/test_concurrency.py"
```
"""
import enum
import random
import uuid
from typing import Callable

from hades.core.event import Event, ProcessUnregistered, SimulationStarted

AddEventCallback = Callable[["Process", Event], None]


class NotificationResponse(enum.Enum):
    ACK = 1  # Acknowledged - the event is handled and acted on
    ACK_BUT_IGNORED = 2  # e.g. the event is handled but some identifier doesn't match so is not processes
    NO_ACK = 3  # the event is not handled in any way


class Process:
    def __init__(self) -> None:
        self.add_event_to_hades: None | AddEventCallback = None
        self._random_process_identifier: int = -1
        self._str: str | None = None

    @property
    def process_name(self):
        return self.__class__.__name__

    @property
    def instance_identifier(self) -> str:
        """
        unique identifier for the process. This does not need to be globally unique however, multiple instances of a given process_name
        with the same instance identifier will not be allowed across the styx (into hades)
        """
        return str(self._random_process_identifier)

    def __str__(self) -> str:
        if self._random_process_identifier != -1:
            return f"process: {self.process_name}, instance: {self.instance_identifier}"
        if self._str is None:
            self._str = f"process: {self.process_name}, instance: {self.instance_identifier}"
        return self._str

    def add_event(self, event: Event):
        if self.add_event_to_hades is None:
            raise ValueError(
                f"add event to hades callback must be set before {self.process_name} can add events to the world"
            )
        self.add_event_to_hades(self, event)

    async def notify(self, event: Event) -> NotificationResponse:
        raise NotImplementedError(f"notify must be implemented for {self.process_name} processes")


class HadesInternalProcess(Process):
    @property
    def instance_identifier(self):
        return super().instance_identifier

    async def notify(self, event: Event) -> NotificationResponse:
        return NotificationResponse.NO_ACK


class PredefinedEventAdder(Process):
    """adds some predefined events to hades then unregisters itself to avoid any overhead"""

    def __init__(self, predefined_events: list[Event], name: str) -> None:
        super().__init__()
        self._name = name
        self._events = predefined_events

    @property
    def instance_identifier(self):
        return self._name

    async def notify(self, event: Event) -> NotificationResponse:
        match event:
            case SimulationStarted(t=t):
                for event in self._events:
                    self.add_event(event)
                self.add_event(ProcessUnregistered(t=t))
                return NotificationResponse.ACK
        return NotificationResponse.NO_ACK


class RandomProcess(Process):
    """a process which adds a .random attribute with the given seed"""

    def __init__(self, seed: str | None) -> None:
        super().__init__()
        self.random = random.Random(seed or self._random_process_identifier)

    def _generate_uuid(self, version: int = 4) -> uuid.UUID:
        """generate a uuid using the random seed"""
        return uuid.UUID(int=self.random.getrandbits(128), version=version)
