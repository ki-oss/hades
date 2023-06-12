"""
`Hades` the core simulation class, responsible for registering `processes`, managing the `event` priority queue, and distributing messages to 
the `processes`. 
"""

import asyncio
import logging
import random
from itertools import count, product
from queue import Empty, PriorityQueue
from typing import Any, Coroutine, Generator, Iterator

from hades.core.event import Event, ProcessUnregistered, SimulationStarted
from hades.core.process import HadesInternalProcess, NotificationResponse, Process

_logger = logging.getLogger(__name__)


class Hades:
    def __init__(
        self,
        random_pomegranate_seed: str | None = "hades",
        max_queue_size: int = 0,
        batch_event_notification_timeout: int | None = 60 * 5,
        record_results: bool = True,
        use_no_ack_cache: bool = False,
    ) -> None:
        self.random = random.Random(random_pomegranate_seed)
        self.event_queue: PriorityQueue = PriorityQueue(maxsize=max_queue_size)
        self.t = 0
        self._processes: list[Process] = []
        self._batch_event_notification_timeout = batch_event_notification_timeout
        self.event_history: list[tuple[tuple[Event, Process], ...]] = []
        self.event_results: dict[tuple[Event, str, str], dict[tuple[str, str], NotificationResponse]] = {}
        self._event_count = count()
        self._record_results = record_results
        self._use_no_ack_cache = use_no_ack_cache
        self._no_ack_cache: set[tuple[str, str]] = set()

    def add_event(self, process: Process, event: Event):
        if self.t > event.t:
            raise ValueError(f"cannot create events in the past {event=} from {process=}")
        queue_event = (event.t, next(self._event_count), (event, process))
        _logger.debug("adding %s from %s to queue", event.name, process)
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

    def _get_events_for_next_timestep(self) -> list[tuple[Event, Process]]:
        """get the next set of events from the event queue and, if the time of those events is different to the current time, change that time"""
        _logger.debug("getting events for next timestamp")
        events = []
        first_event = None
        while True:
            try:
                t, tie_break, (event, process) = self.event_queue.get(timeout=0)
            except Empty:
                break
            if first_event is None:
                first_event = event
                if first_event.t != self.t:
                    _logger.debug("time moved to %d", first_event.t)
                    self.t = first_event.t
            elif event.t != first_event.t:
                # put it back on! for the next timestep
                self.event_queue.put((t, tie_break, (event, process)))
                break
            _logger.debug(f"added {event=} to next events batch")
            events.append((event, process))
        _logger.debug("got %d events at time %d", len(events), self.t)
        return events

    def _get_processor_event_notification_coroutines(
        self, target_process_events_and_source_processes: list[tuple[Event, Process, Process]]
    ) -> list[Coroutine[Any, Any, NotificationResponse]]:
        """broadcast all events to all processes"""
        tasks = []
        for event, _, target_process in target_process_events_and_source_processes:
            tasks.append(asyncio.wait_for(target_process.notify(event), timeout=self._batch_event_notification_timeout))
        return tasks

    def _handle_unregister_events(self, events: list[tuple[Event, Process]]):
        """handle the special ProcessUnregistered event"""
        for event, process in events:
            if event.name == ProcessUnregistered.__name__:
                self.unregister_process(process)

    def _handle_event_results(
        self,
        results: list[tuple[Event, Process]],
        event_source_targets: list[tuple[Event, Process, Process]],
    ):
        exception_to_raise = None
        for result, (event, source_process, target_process) in zip(
            results, event_source_targets
        ):
            _logger.debug(
                f"completed task notify %s of %s from %s with result %s", target_process, event, source_process, result
            )
            if isinstance(result, Exception):
                if exception_to_raise is not None:
                    try:
                        raise exception_to_raise
                    except Exception:
                        _logger.exception("error with %s of %s from %s with result %s", target_process, event, source_process, result)
                exception_to_raise = result
                continue
            notification_response = result
            if not isinstance(notification_response, NotificationResponse):
                if exception_to_raise is not None:
                    try:
                        raise exception_to_raise
                    except Exception:
                        _logger.exception("error with %s of %s from %s with result %s", target_process, event, source_process, result)
                exception_to_raise = TypeError(
                    "unexpected notification response. Expected NotificationResponse but got"
                    f" {type(notification_response)} when sending {event} to {target_process} from {source_process}"
                )
                continue
            if self._use_no_ack_cache and result == NotificationResponse.NO_ACK:
                self._no_ack_cache.add((event.name, str(target_process)))
            if self._record_results:
                try:
                    self.event_results[(event, source_process.process_name, source_process.instance_identifier)][
                        (target_process.process_name, target_process.instance_identifier)
                    ] = notification_response
                except KeyError:
                    self.event_results[(event, source_process.process_name, source_process.instance_identifier)] = {
                        (target_process.process_name, target_process.instance_identifier): notification_response
                    }

        if exception_to_raise:
            raise exception_to_raise

    async def step(self, until: int | None = None) -> bool:
        events_for_timestep = self._get_events_for_next_timestep()
        if not events_for_timestep:
            _logger.info("ending run as we have exhausted the queue of events!")
            return False
        elif until is not None and self.t > until:
            _logger.info("ending run as we reached events occurring beyond the end of time (%d)!", until)
            return False

        self._handle_unregister_events(events_for_timestep)

        self.event_history.append(tuple(events_for_timestep))
        target_process_events_and_source_processes = [
            (event, source_process, target_process)
            for target_process, (event, source_process) in product(self._processes, events_for_timestep)
            if not self._use_no_ack_cache or (event.name, str(target_process)) not in self._no_ack_cache
        ]
        processor_event_notifications = self._get_processor_event_notification_coroutines(
            target_process_events_and_source_processes
        )
        results = await asyncio.gather(*processor_event_notifications, return_exceptions=True)
        self._handle_event_results(results, target_process_events_and_source_processes)

        return True

    async def run(self, until: int | None = None):
        hades_process = HadesInternalProcess()
        self.register_process(hades_process)
        self.add_event(hades_process, SimulationStarted())
        continue_running = True
        while continue_running:
            continue_running = await self.step(until=until)
