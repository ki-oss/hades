"""
The entity doing the main body of work within the simulation is the `Process`. The `notify(event)` method of every process registered 
(via `hades_instance.register_process()`) will be called for each event in the queue for the next time step as a group of asynchronous tasks.
That is to say: events are broadcast and handled asynchronously by the registered processes. 
For justification of this see the [design justification](./design-justification.md).

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
"""
import enum
import random
import uuid
from typing import Callable

from .event import Event, ProcessUnregistered, SimulationStarted

AddEventCallback = Callable[["Process", Event], None]


class NotificationResponse(enum.Enum):
    ACK = 1  # Acknowledged - the event is handled and acted on
    ACK_BUT_IGNORED = 2  # e.g. the event is handled but some identifier doesn't match so is not processes
    NO_ACK = 3  # the event is not handled in any way


class Process:
    def __init__(self) -> None:
        self.add_event_to_hades: None | AddEventCallback = None
        self._random_process_identifier: int = -1

    @property
    def process_name(self):
        return self.__class__.__name__

    @property
    def instance_identifier(self) -> str:
        """
        unique identifier for the process. This does not need to be globally unique for items in memory (like id()) say
        however, multiple instances of a given process_name with the same instance identifier will not be allowed across the styx (into hades)
        """
        return str(self._random_process_identifier)

    def __str__(self) -> str:
        return f"process: {self.process_name}, instance: {self.instance_identifier}"

    def add_event(self, event: Event):
        if self.add_event_to_hades is None:
            raise ValueError(
                f"add event to hades callback must be set before {self.process_name} can add events to the world"
            )
        self.add_event_to_hades(self, event)

    async def notify(self, event: Event) -> NotificationResponse:
        # TODO: perhaps add optional reasons to notification responses - e.g. to distinguish between different types of IGNORES
        raise NotImplementedError(f"notify must be implemented for {self.process_name} processes")

    # TODO: scrape method exposing prometheus metrics belonging to the process


class HadesInternalProcess(Process):
    @property
    def instance_identifier(self):
        return super().instance_identifier

    async def notify(self, event: Event) -> NotificationResponse:
        return NotificationResponse.NO_ACK


class PredefinedEventAdder(Process):
    """adds some predefined events to hades then unregisters itself"""

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
    def __init__(self, seed: str | None) -> None:
        super().__init__()
        self.random = random.Random(seed or self._random_process_identifier)

    def _generate_uuid(self, version: int = 4) -> uuid.UUID:
        return uuid.UUID(int=self.random.getrandbits(128), version=version)
