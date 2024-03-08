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
import logging
from asyncio.exceptions import TimeoutError

import websockets
from websockets.exceptions import ConnectionClosedOK

from hades import Hades, NotificationResponse
from hades.time import QuarterStartScheduler, YearStartScheduler
from hades.visualisation.websockets import HadesWS, WebSocketProcess

connected = set()
clients = set()


async def serve(websocket):
    clients.add(websocket)
    while True:
        try:
            message = await websocket.recv()
            # this is the WebSocketProcess so we can remove it
            for connection in clients:
                await connection.send(message)
        except websockets.ConnectionClosedOK:
            break


async def test_websockets_process_ignores_non_events():
    assert await WebSocketProcess(None).notify(None) == NotificationResponse.NO_ACK


async def test_websockets_process_broadcasts_correct_events():
    broadcasted_messages = []
    async with websockets.serve(serve, "localhost", 8765):
        hades = Hades()
        hades.register_process(YearStartScheduler(start_year=2022, look_ahead_years=2))
        hades.register_process(QuarterStartScheduler())
        ws_process_connection = await websockets.connect("ws://localhost:8765")
        hades.register_process(WebSocketProcess(ws_process_connection))
        client_connection = await websockets.connect("ws://localhost:8765")
        await hades.run()
        try:
            while message := await asyncio.wait_for(client_connection.recv(), timeout=0.5):
                broadcasted_messages.append(message)
        except TimeoutError:
            pass
    assert broadcasted_messages == [
        '{"event_type": "SimulationStarted", "event_contents": {"t": 0}}',
        '{"event_type": "YearStarted", "event_contents": {"t": 738155}}',
        '{"event_type": "QuarterStarted", "event_contents": {"t": 738155}}',
        '{"event_type": "QuarterStarted", "event_contents": {"t": 738245}}',
        '{"event_type": "QuarterStarted", "event_contents": {"t": 738336}}',
        '{"event_type": "QuarterStarted", "event_contents": {"t": 738428}}',
        '{"event_type": "YearStarted", "event_contents": {"t": 738520}}',
        '{"event_type": "QuarterStarted", "event_contents": {"t": 738520}}',
        '{"event_type": "QuarterStarted", "event_contents": {"t": 738610}}',
        '{"event_type": "QuarterStarted", "event_contents": {"t": 738701}}',
        '{"event_type": "QuarterStarted", "event_contents": {"t": 738793}}',
        '{"event_type": "SimulationEnded", "event_contents": {"t": 738793}}',
    ]


async def test_hades_websockets(caplog):
    caplog.set_level(logging.DEBUG)
    broadcasted_messages = []
    hades = HadesWS()
    hades.register_process(YearStartScheduler(start_year=2022, look_ahead_years=2))
    hades.register_process(QuarterStartScheduler())

    async def connect_after_a_while():
        await asyncio.sleep(0.5)
        client_connection = await websockets.connect("ws://localhost:8765")
        await client_connection.send("hi im a client")
        try:
            while message := await asyncio.wait_for(client_connection.recv(), timeout=10):
                broadcasted_messages.append(message)
        except (TimeoutError, ConnectionClosedOK):
            pass

    await asyncio.gather(hades.run(), connect_after_a_while())

    assert broadcasted_messages == [
        (
            '{"source_process": {"process_name": "HadesInternalProcess", "instance_identifier":'
            ' "7970269937446031133269215595648805179"}, "target_process": {"process_name": "YearStartScheduler",'
            ' "instance_identifier": "332231294394531790607923355838092946842"}, "event": {"event_type":'
            ' "SimulationStarted", "event_contents": {"t": 0}}, "target_process_response": 1, "causing_event": null}'
        ),
        (
            '{"source_process": {"process_name": "HadesInternalProcess", "instance_identifier":'
            ' "7970269937446031133269215595648805179"}, "target_process": {"process_name": "QuarterStartScheduler",'
            ' "instance_identifier": "7836064115094481643618470001379502846"}, "event": {"event_type":'
            ' "SimulationStarted", "event_contents": {"t": 0}}, "target_process_response": 3, "causing_event": null}'
        ),
        (
            '{"source_process": {"process_name": "HadesInternalProcess", "instance_identifier":'
            ' "7970269937446031133269215595648805179"}, "target_process": {"process_name": "HadesInternalProcess",'
            ' "instance_identifier": "7970269937446031133269215595648805179"}, "event": {"event_type":'
            ' "SimulationStarted", "event_contents": {"t": 0}}, "target_process_response": 3, "causing_event": null}'
        ),
        (
            '{"source_process": {"process_name": "YearStartScheduler", "instance_identifier":'
            ' "332231294394531790607923355838092946842"}, "target_process": {"process_name": "YearStartScheduler",'
            ' "instance_identifier": "332231294394531790607923355838092946842"}, "event": {"event_type": "YearStarted",'
            ' "event_contents": {"t": 738155}}, "target_process_response": 2, "causing_event": {"event_type":'
            ' "SimulationStarted", "event_contents": {"t": 0}}}'
        ),
        (
            '{"source_process": {"process_name": "YearStartScheduler", "instance_identifier":'
            ' "332231294394531790607923355838092946842"}, "target_process": {"process_name": "QuarterStartScheduler",'
            ' "instance_identifier": "7836064115094481643618470001379502846"}, "event": {"event_type": "YearStarted",'
            ' "event_contents": {"t": 738155}}, "target_process_response": 1, "causing_event": {"event_type":'
            ' "SimulationStarted", "event_contents": {"t": 0}}}'
        ),
        (
            '{"source_process": {"process_name": "YearStartScheduler", "instance_identifier":'
            ' "332231294394531790607923355838092946842"}, "target_process": {"process_name": "HadesInternalProcess",'
            ' "instance_identifier": "7970269937446031133269215595648805179"}, "event": {"event_type": "YearStarted",'
            ' "event_contents": {"t": 738155}}, "target_process_response": 3, "causing_event": {"event_type":'
            ' "SimulationStarted", "event_contents": {"t": 0}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "YearStartScheduler",'
            ' "instance_identifier": "332231294394531790607923355838092946842"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738155}}, "target_process_response": 2, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738155}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "QuarterStartScheduler",'
            ' "instance_identifier": "7836064115094481643618470001379502846"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738155}}, "target_process_response": 3, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738155}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "HadesInternalProcess",'
            ' "instance_identifier": "7970269937446031133269215595648805179"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738155}}, "target_process_response": 3, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738155}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "YearStartScheduler",'
            ' "instance_identifier": "332231294394531790607923355838092946842"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738245}}, "target_process_response": 2, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738155}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "QuarterStartScheduler",'
            ' "instance_identifier": "7836064115094481643618470001379502846"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738245}}, "target_process_response": 3, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738155}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "HadesInternalProcess",'
            ' "instance_identifier": "7970269937446031133269215595648805179"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738245}}, "target_process_response": 3, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738155}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "YearStartScheduler",'
            ' "instance_identifier": "332231294394531790607923355838092946842"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738336}}, "target_process_response": 2, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738155}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "QuarterStartScheduler",'
            ' "instance_identifier": "7836064115094481643618470001379502846"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738336}}, "target_process_response": 3, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738155}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "HadesInternalProcess",'
            ' "instance_identifier": "7970269937446031133269215595648805179"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738336}}, "target_process_response": 3, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738155}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "YearStartScheduler",'
            ' "instance_identifier": "332231294394531790607923355838092946842"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738428}}, "target_process_response": 2, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738155}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "QuarterStartScheduler",'
            ' "instance_identifier": "7836064115094481643618470001379502846"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738428}}, "target_process_response": 3, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738155}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "HadesInternalProcess",'
            ' "instance_identifier": "7970269937446031133269215595648805179"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738428}}, "target_process_response": 3, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738155}}}'
        ),
        (
            '{"source_process": {"process_name": "YearStartScheduler", "instance_identifier":'
            ' "332231294394531790607923355838092946842"}, "target_process": {"process_name": "YearStartScheduler",'
            ' "instance_identifier": "332231294394531790607923355838092946842"}, "event": {"event_type": "YearStarted",'
            ' "event_contents": {"t": 738520}}, "target_process_response": 2, "causing_event": {"event_type":'
            ' "SimulationStarted", "event_contents": {"t": 0}}}'
        ),
        (
            '{"source_process": {"process_name": "YearStartScheduler", "instance_identifier":'
            ' "332231294394531790607923355838092946842"}, "target_process": {"process_name": "QuarterStartScheduler",'
            ' "instance_identifier": "7836064115094481643618470001379502846"}, "event": {"event_type": "YearStarted",'
            ' "event_contents": {"t": 738520}}, "target_process_response": 1, "causing_event": {"event_type":'
            ' "SimulationStarted", "event_contents": {"t": 0}}}'
        ),
        (
            '{"source_process": {"process_name": "YearStartScheduler", "instance_identifier":'
            ' "332231294394531790607923355838092946842"}, "target_process": {"process_name": "HadesInternalProcess",'
            ' "instance_identifier": "7970269937446031133269215595648805179"}, "event": {"event_type": "YearStarted",'
            ' "event_contents": {"t": 738520}}, "target_process_response": 3, "causing_event": {"event_type":'
            ' "SimulationStarted", "event_contents": {"t": 0}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "YearStartScheduler",'
            ' "instance_identifier": "332231294394531790607923355838092946842"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738520}}, "target_process_response": 2, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738520}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "QuarterStartScheduler",'
            ' "instance_identifier": "7836064115094481643618470001379502846"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738520}}, "target_process_response": 3, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738520}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "HadesInternalProcess",'
            ' "instance_identifier": "7970269937446031133269215595648805179"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738520}}, "target_process_response": 3, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738520}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "YearStartScheduler",'
            ' "instance_identifier": "332231294394531790607923355838092946842"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738610}}, "target_process_response": 2, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738520}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "QuarterStartScheduler",'
            ' "instance_identifier": "7836064115094481643618470001379502846"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738610}}, "target_process_response": 3, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738520}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "HadesInternalProcess",'
            ' "instance_identifier": "7970269937446031133269215595648805179"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738610}}, "target_process_response": 3, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738520}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "YearStartScheduler",'
            ' "instance_identifier": "332231294394531790607923355838092946842"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738701}}, "target_process_response": 2, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738520}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "QuarterStartScheduler",'
            ' "instance_identifier": "7836064115094481643618470001379502846"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738701}}, "target_process_response": 3, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738520}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "HadesInternalProcess",'
            ' "instance_identifier": "7970269937446031133269215595648805179"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738701}}, "target_process_response": 3, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738520}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "YearStartScheduler",'
            ' "instance_identifier": "332231294394531790607923355838092946842"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738793}}, "target_process_response": 2, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738520}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "QuarterStartScheduler",'
            ' "instance_identifier": "7836064115094481643618470001379502846"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738793}}, "target_process_response": 3, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738520}}}'
        ),
        (
            '{"source_process": {"process_name": "QuarterStartScheduler", "instance_identifier":'
            ' "7836064115094481643618470001379502846"}, "target_process": {"process_name": "HadesInternalProcess",'
            ' "instance_identifier": "7970269937446031133269215595648805179"}, "event": {"event_type":'
            ' "QuarterStarted", "event_contents": {"t": 738793}}, "target_process_response": 3, "causing_event":'
            ' {"event_type": "YearStarted", "event_contents": {"t": 738520}}}'
        ),
        (
            '{"source_process": {"process_name": "HadesInternalProcess", '
            '"instance_identifier": "7970269937446031133269215595648805179"}, '
            '"target_process": {"process_name": "YearStartScheduler", '
            '"instance_identifier": "332231294394531790607923355838092946842"}, "event": '
            '{"event_type": "SimulationEnded", "event_contents": {"t": 738793}}, '
            '"target_process_response": 1, "causing_event": null}'
        ),
        (
            '{"source_process": {"process_name": "HadesInternalProcess", '
            '"instance_identifier": "7970269937446031133269215595648805179"}, '
            '"target_process": {"process_name": "QuarterStartScheduler", '
            '"instance_identifier": "7836064115094481643618470001379502846"}, "event": '
            '{"event_type": "SimulationEnded", "event_contents": {"t": 738793}}, '
            '"target_process_response": 3, "causing_event": null}'
        ),
        (
            '{"source_process": {"process_name": "HadesInternalProcess", '
            '"instance_identifier": "7970269937446031133269215595648805179"}, '
            '"target_process": {"process_name": "HadesInternalProcess", '
            '"instance_identifier": "7970269937446031133269215595648805179"}, "event": '
            '{"event_type": "SimulationEnded", "event_contents": {"t": 738793}}, '
            '"target_process_response": 3, "causing_event": null}'
        ),
    ]

    assert "hi im a client" in caplog.text
