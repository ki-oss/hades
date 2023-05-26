"""
`Hades` the core simulation class, responsible for registering `processes`, managing the `event` priority queue, and distributing messages to 
the `processes`. 
"""

import asyncio
import logging
import random
from itertools import count
from queue import Empty, PriorityQueue
from typing import Iterable, List, Optional

from .event import Event, ProcessUnregistered, SimulationStarted
from .process import HadesInternalProcess, NotificationResponse, Process

_logger = logging.getLogger(__name__)


def serialize_event(process: Process, event: Event, event_index: int) -> str:
    return f"{process.process_name},{process.instance_identifier},{event.name},{event_index}"


def deserialize_event(serialized_event: str) -> tuple[str, str, str, int]:
    target_process, target_process_instance, event, event_index = serialized_event.split(",")
    return target_process, target_process_instance, event, int(event_index)


class Hades:
    def __init__(
        self,
        random_pomegranate_seed: str = "hades",
        max_queue_size: int = 0,
        batch_event_notification_timeout: int = 60 * 5,
        logger: Optional[logging.Logger] = None,
        logging_filters: Optional[Iterable[logging.Filter]] = None,
        logging_handlers: Optional[Iterable[logging.Handler]] = None,
    ) -> None:
        if random_pomegranate_seed:
            self.random = random.Random(random_pomegranate_seed)
        else:
            self.random = random.Random()
        self.event_queue: PriorityQueue = PriorityQueue(maxsize=max_queue_size)
        self.t = 0
        self._processes: list[Process] = []
        self._batch_event_notification_timeout = batch_event_notification_timeout
        self.event_history: list[tuple[tuple[Event, Process], ...]] = []
        self.event_results: dict[tuple[Event, str, str], dict[tuple[str, str], NotificationResponse]] = {}
        self._event_count = count()

        if logger is None:
            self._logger = _logger
        else:
            self._logger = logger

        for filter in logging_filters or []:
            self._logger.addFilter(filter)
        for handler in logging_handlers or []:
            self._logger.addHandler(handler)

    def add_event(self, process: Process, event: Event):
        if self.t > event.t:
            raise ValueError("cannot create events in the past")
        queue_event = (event.t, next(self._event_count), (event, process))
        self._logger.debug(f"adding {queue_event=} to queue")
        self.event_queue.put(queue_event)

    def register_process(self, process: Process):
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
        if process.instance_identifier == -1:
            process._random_process_identifier = self.random.getrandbits(128)
        self._processes.append(process)
        self._logger.info(f"registered {process.process_name}: {process.instance_identifier}")

    def unregister_process(self, process: Process):
        self._logger.info(f"unregistered {process.process_name}: {process.instance_identifier}")
        self._processes = [
            existing_process for existing_process in self._processes if id(existing_process) != id(process)
        ]

    def _get_events_for_next_timestep(self) -> List[tuple[Event, Process]]:
        self._logger.debug("getting events for next timestamp")
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
                    self._logger.debug(f"time moved to {first_event.t}")
                    self.t = first_event.t
            elif event.t != first_event.t:
                # put it back on! for the next timestep
                self.event_queue.put((t, tie_break, (event, process)))
                break
            self._logger.debug(f"added {event=} to next events batch")
            events.append((event, process))
        self._logger.debug(f"got {len(events)} events at time {self.t}")
        return events

    def _get_processor_event_notification_coroutines(
        self, events: List[Event]
    ) -> List[asyncio.Task[NotificationResponse]]:
        """broadcast all events to all processes"""
        tasks = []
        for process in self._processes:
            for event_index, event in enumerate(events):
                try:
                    name = serialize_event(process, event, event_index)
                except TypeError:
                    _logger.error(f"could not serialize {event} being sent to {process}")
                    raise
                tasks.append(asyncio.create_task(process.notify(event), name=name))
        return tasks

    def _handle_unregister_events(self, events: List[tuple[Event, Process]]):
        for event, process in events:
            if event.name == ProcessUnregistered.name:
                self.unregister_process(process)

    async def run(self, until: Optional[int] = None):
        hades_process = HadesInternalProcess()
        self.register_process(hades_process)
        self.add_event(hades_process, SimulationStarted())
        while True:
            events_for_timestep = self._get_events_for_next_timestep()
            if not events_for_timestep:
                self._logger.info("ending run as we have exhausted the queue of events!")
                break
            elif until is not None and self.t > until:
                self._logger.info(f"ending run as we reached events occurring beyond the end of time ({until})!")
                break

            pure_events = [event for event, _ in events_for_timestep]
            self._handle_unregister_events(events_for_timestep)

            self.event_history.append(tuple(events_for_timestep))

            processor_event_notifications = self._get_processor_event_notification_coroutines(events=pure_events)
            done, pending = await asyncio.wait(
                processor_event_notifications,
                timeout=self._batch_event_notification_timeout,
                return_when=asyncio.ALL_COMPLETED,
            )
            exceptions_to_raise: List[tuple[BaseException, str]] = []
            for task in done:
                task_name = task.get_name()
                self._logger.debug(f"completed task: {task_name}")
                if exc := task.exception():
                    exceptions_to_raise.append((exc, task_name))
                    continue
                target_process_name, target_process_instance, _, event_index = deserialize_event(task_name)
                notification_response = task.result()
                if not isinstance(notification_response, NotificationResponse):
                    exceptions_to_raise.append(
                        (
                            TypeError(
                                "unexpected notification response. Expected NotificationResponse but got"
                                f" {type(notification_response)}"
                            ),
                            task_name,
                        )
                    )
                    continue
                event, process = events_for_timestep[event_index]
                target_process: tuple[str, str] = (target_process_name, target_process_instance)
                try:
                    self.event_results[(event, process.process_name, process.instance_identifier)][
                        target_process
                    ] = notification_response
                except KeyError:
                    self.event_results[(event, process.process_name, process.instance_identifier)] = {
                        target_process: notification_response
                    }

            for task in pending:
                self._logger.error(f"cancelling task: {task.get_name()} as it timed out")
                task.cancel()
            if pending:
                raise TimeoutError
            for i, (exc, task_name) in enumerate(exceptions_to_raise):
                if i == len(exceptions_to_raise) - 1:
                    raise exc
                try:
                    raise exc
                except Exception:
                    _logger.exception(f"got additional exception (not raised) as part of batch from {task_name}")
