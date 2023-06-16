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
`Hades` the core simulation class, responsible for registering `processes`, managing the `event` priority queue, and distributing messages to 
the `processes`. 
"""

import asyncio
import inspect
import logging
import random
from itertools import count, product
from queue import Empty, PriorityQueue
from typing import Any, Coroutine

from hades.core.event import Event, ProcessUnregistered, SimulationStarted
from hades.core.process import HadesInternalProcess, NotificationResponse, Process

_logger = logging.getLogger(__name__)


QueuedEvent = tuple[Event, Process, Event | None]
EventSourceTargetCause = tuple[Event, Process, Process, Event | None]


class Hades:
    def __init__(
        self,
        random_pomegranate_seed: str | None = "hades",
        max_queue_size: int = 0,
        batch_event_notification_timeout: int | None = 60 * 5,
        record_results: bool = True,
        record_event_history: bool = True,
        use_no_ack_cache: bool = False,
        track_causing_events: bool = False,
    ) -> None:
        """Hades initialisation, specify core simulation parameters and performance optimisations

        Args:
            random_pomegranate_seed (str | None, optional): a random seed, used to initialise process instance identifiers etc. Defaults to "hades".
            max_queue_size (int, optional): how large the event queue is allowed to grow to, infinite by default. Defaults to 0.
            batch_event_notification_timeout (int | None, optional): how long to wait for a batch of events (at a timestep) before erroring. Defaults to 60*5.
            record_results (bool, optional): performance measure - whether to record process responses to events in self._event_results. Defaults to True.
            record_event_history (bool, optional): performance measure - whether to record event history in self.event_history. Defaults to True.
            use_no_ack_cache (bool, optional): performance measure - whether to stop notifying target processes of event types once they respond with a NO_ACK to one. Defaults to False.
            track_causing_events (bool, optional): performance measure - whether to track which events caused other events, may be useful for downstream visualisation but not required functionally. Defaults to False.
        """
        self.random = random.Random(random_pomegranate_seed)
        self.event_queue: PriorityQueue = PriorityQueue(maxsize=max_queue_size)
        self.t = 0
        self._processes: list[Process] = []
        self._batch_event_notification_timeout = batch_event_notification_timeout
        self.event_history: list[tuple[tuple[Event, Process, Event | None], ...]] = []
        self.event_results: dict[tuple[Event, str, str, Event | None], dict[tuple[str, str], NotificationResponse]] = {}

        self._event_count = count()
        self._record_results = record_results
        self._record_event_history = record_event_history
        self._use_no_ack_cache = use_no_ack_cache
        self._track_causing_event = track_causing_events
        self._no_ack_cache: set[tuple[str, str]] = set()

    def add_event(self, process: Process, event: Event):
        if self.t > event.t:
            raise ValueError(f"cannot create events in the past {event=} from {process=}")
        causing_event = None
        # look up the event which caused this event to exist
        if self._track_causing_event:
            current_frame = inspect.currentframe()
            if not current_frame or not current_frame.f_back or not current_frame.f_back.f_back:
                raise ValueError("could not causing event")

            caller_frame = current_frame.f_back.f_back
            caller_arguments = inspect.getargvalues(caller_frame)
            if not isinstance(caller_arguments, inspect.ArgInfo):
                raise TypeError(f"bad caller arguments {caller_arguments}")
            if caller_arguments.locals["self"] is process:
                causing_event = caller_arguments.locals.get("event")

        queue_event = (event.t, next(self._event_count), (event, process, causing_event))
        _logger.debug("adding %s from %s (caused by %s) to queue", event.name, process, causing_event)
        self.event_queue.put(queue_event)

    def register_process(self, process: Process):
        if process.instance_identifier == "-1":
            process._random_process_identifier = self.random.getrandbits(128)

        for existing_process in self._processes:
            if (
                existing_process.instance_identifier == process.instance_identifier
                and existing_process.process_name == process.process_name
            ):
                raise ValueError(
                    f"process {process.process_name}: {process.instance_identifier} already exists within the"
                    " environment, cannot add twice"
                )

        process.add_event_to_hades = self.add_event

        self._processes.append(process)
        _logger.info(f"registered %s", process)

    def unregister_process(self, process: Process):
        _logger.info("unregistered %s", process)
        self._processes = [
            existing_process for existing_process in self._processes if id(existing_process) != id(process)
        ]

    def _get_events_for_next_timestep(self) -> list[QueuedEvent]:
        """get the next set of events from the event queue and, if the time of those events is different to the current time, change that time"""
        _logger.debug("getting events for next timestamp")
        events = []
        first_event = None
        while True:
            try:
                next_item = self.event_queue.get(timeout=0)
                t, tie_break, (event, process, causing_event) = next_item
            except Empty:
                break

            if first_event is None:
                first_event = event
                if first_event.t != self.t:
                    _logger.debug("time moved to %d", first_event.t)
                    self.t = first_event.t
            elif event.t != first_event.t:
                # put it back on! for the next timestep
                self.event_queue.put((t, tie_break, (event, process, causing_event)))
                break
            _logger.debug(f"added event=%s to next events batch", repr(event))
            events.append((event, process, causing_event))
        _logger.debug("got %d events at time %d", len(events), self.t)
        return events

    def _get_processor_event_notification_coroutines(
        self, target_process_events_and_source_processes: list[EventSourceTargetCause]
    ) -> list[Coroutine[Any, Any, NotificationResponse]]:
        """create notify tasks with timeouts"""
        tasks = []
        for event, _, target_process, _ in target_process_events_and_source_processes:
            tasks.append(asyncio.wait_for(target_process.notify(event), timeout=self._batch_event_notification_timeout))
        return tasks

    def _handle_unregister_events(self, events: list[QueuedEvent]):
        """handle the special ProcessUnregistered event"""
        for event, process, _ in events:
            if event.name == ProcessUnregistered.__name__:
                self.unregister_process(process)

    async def _handle_event_results(
        self,
        results: list[NotificationResponse | Exception],
        event_source_targets: list[EventSourceTargetCause],
    ):
        exception_to_raise = None
        for result, (event, source_process, target_process, causing_event) in zip(results, event_source_targets):
            _logger.debug(
                f"completed task notify %s of %s from %s with result %s", target_process, event, source_process, result
            )
            if isinstance(result, Exception):
                if exception_to_raise is not None:
                    try:
                        raise exception_to_raise
                    except Exception:
                        _logger.exception(
                            "error with %s of %s from %s with result %s", target_process, event, source_process, result
                        )
                exception_to_raise = result
                continue
            notification_response = result
            if not isinstance(notification_response, NotificationResponse):
                if exception_to_raise is not None:
                    try:
                        raise exception_to_raise
                    except Exception:
                        _logger.exception(
                            "error with %s of %s from %s with result %s", target_process, event, source_process, result
                        )
                exception_to_raise = TypeError(
                    "unexpected notification response. Expected NotificationResponse but got"
                    f" {type(notification_response)} when sending {event} to {target_process} from {source_process}"
                )
                continue
            if self._use_no_ack_cache and result == NotificationResponse.NO_ACK:
                self._no_ack_cache.add((event.name, str(target_process)))
            if self._record_results:
                key = (event, source_process.process_name, source_process.instance_identifier, causing_event)
                try:
                    self.event_results[key][
                        (target_process.process_name, target_process.instance_identifier)
                    ] = notification_response
                except KeyError:
                    self.event_results[key] = {
                        (target_process.process_name, target_process.instance_identifier): notification_response
                    }

        if exception_to_raise:
            raise exception_to_raise

    async def _broadcast_events(
        self, target_process_events_and_source_processes
    ) -> list[NotificationResponse | Exception]:
        processor_event_notifications = self._get_processor_event_notification_coroutines(
            target_process_events_and_source_processes
        )
        return await asyncio.gather(*processor_event_notifications, return_exceptions=True)

    async def step(self, until: int | None = None) -> bool:
        events_for_timestep = self._get_events_for_next_timestep()
        if not events_for_timestep:
            _logger.info("ending run as we have exhausted the queue of events!")
            return False
        elif until is not None and self.t > until:
            _logger.info("ending run as we reached events occurring beyond the end of time (%d)!", until)
            return False

        self._handle_unregister_events(events_for_timestep)
        if self._record_event_history:
            self.event_history.append(tuple(events_for_timestep))
        target_process_events_and_source_processes = [
            (event, source_process, target_process, cause)
            for target_process, (event, source_process, cause) in product(self._processes, events_for_timestep)
            if not self._use_no_ack_cache or (event.name, str(target_process)) not in self._no_ack_cache
        ]
        results = await self._broadcast_events(target_process_events_and_source_processes)
        await self._handle_event_results(results, target_process_events_and_source_processes)

        return True

    async def run(self, until: int | None = None):
        hades_process = HadesInternalProcess()
        self.register_process(hades_process)
        self.add_event(hades_process, SimulationStarted())
        continue_running = True
        while continue_running:
            continue_running = await self.step(until=until)
