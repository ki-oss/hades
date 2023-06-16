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

"""output events or event results to websockets for live visualisation using custom frontend TS/JS code or other clients"""
import asyncio
import logging
from typing import Any

import websockets
from pydantic import BaseModel
from websockets.exceptions import ConnectionClosed

from hades import Hades, Process
from hades.core.event import Event
from hades.core.hades import EventSourceTargetCause
from hades.core.process import NotificationResponse, Process

_logger = logging.getLogger(__name__)


class EventWithType(BaseModel):
    event_type: str
    event_contents: Event


class ProcessDetails(BaseModel):
    process_name: str
    instance_identifier: str


class EventContext(BaseModel):
    """full details of an event notification's result"""

    source_process: ProcessDetails
    target_process: ProcessDetails
    event: EventWithType
    target_process_response: NotificationResponse
    causing_event: EventWithType | None


class WebSocketProcess(Process):
    """simple process which sends all the events it receives as JSON to a websockets server
    this could be used for visualisation or monitoring
    """

    def __init__(self, websocket_connection) -> None:
        self._connection = websocket_connection
        super().__init__()

    async def _send_event(self, event: Event):
        await self._connection.send(EventWithType.construct(event_type=event.name, event_contents=event).json())

    async def notify(self, event: Event):
        match event:
            case Event() as e:
                await self._send_event(event)
                return NotificationResponse.ACK
        return NotificationResponse.NO_ACK


class HadesWS(Hades):
    """Hades with a websocket server bundled. Waits for at least one client to connect before starting the simulation"""

    def __init__(
        self,
        random_pomegranate_seed: str | None = "hades",
        max_queue_size: int = 0,
        batch_event_notification_timeout: int | None = 60 * 5,
        record_results: bool = True,
        record_event_history: bool = True,
        use_no_ack_cache: bool = False,
        track_causing_events: bool = True,
        ws_server_host: str = "localhost",
        ws_server_port: int = 8765,
        ws_server=None,
    ) -> None:
        super().__init__(
            random_pomegranate_seed,
            max_queue_size,
            batch_event_notification_timeout,
            record_results,
            record_event_history,
            use_no_ack_cache,
            track_causing_events,
        )
        self._ws_server_host = ws_server_host
        self._ws_server_port = ws_server_port
        self._ws_server = ws_server
        self._ws_clients: set[Any] = set()

    async def ws_server(self, websocket):
        """received client messages"""
        self._ws_clients.add(websocket)
        while True:
            try:
                message = await websocket.recv()
                _logger.debug("received message: %s from ws client", message)
            except ConnectionClosed:
                break

    async def _handle_event_results(
        self,
        results: list[NotificationResponse | Exception],
        event_source_targets: list[EventSourceTargetCause],
    ):
        """asynchronously rebroadcast all event results to all ws clients"""
        rebroadcast_ws_events = []
        for result, (event, source_process, target_process, causing_event) in zip(results, event_source_targets):
            if isinstance(result, NotificationResponse):
                for client in self._ws_clients:
                    rebroadcast_ws_events.append(
                        asyncio.wait_for(
                            client.send(
                                EventContext(
                                    source_process=ProcessDetails.construct(
                                        process_name=source_process.process_name,
                                        instance_identifier=source_process.instance_identifier,
                                    ),
                                    target_process=ProcessDetails.construct(
                                        process_name=target_process.process_name,
                                        instance_identifier=target_process.instance_identifier,
                                    ),
                                    event=EventWithType(event_type=event.name, event_contents=event),
                                    target_process_response=result,
                                    causing_event=(
                                        None
                                        if causing_event is None
                                        else EventWithType(event_type=causing_event.name, event_contents=causing_event)
                                    ),
                                ).json()
                            ),
                            timeout=self._batch_event_notification_timeout,
                        )
                    )
        await asyncio.gather(*rebroadcast_ws_events)
        await super()._handle_event_results(results, event_source_targets)

    async def run(self, until: int | None = None):
        """start a server if none is injected and wait for a client connection"""
        # Start WebSocket server
        if self._ws_server is None:
            self._ws_server = await websockets.serve(self.ws_server, self._ws_server_host, self._ws_server_port)  # type: ignore

        # Wait for at least one client to connect
        while not self._ws_clients:
            await asyncio.sleep(1)  # Wait for 1 second before checking again
        await super().run(until=until)
        self._ws_server.close()
        await self._ws_server.wait_closed()
