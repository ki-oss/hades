import logging

import pytest

from hades import Hades, Process, ProcessUnregistered, SimulationStarted
from hades.core.event import Event
from hades.core.process import HadesInternalProcess, NotificationResponse


def test_cannot_add_events_in_past():
    h = Hades()
    h.t = 10
    with pytest.raises(ValueError):
        h.add_event(Process(), SimulationStarted(t=0))


class UniqueProcess(Process):
    @property
    def instance_identifier(self) -> str:
        return "unicorn"
    
    async def notify(self, event: Event):
        return NotificationResponse.NO_ACK

def test_cannot_add_duplicate_processes():
    h = Hades()
    h.register_process(UniqueProcess())
    with pytest.raises(ValueError):
        h.register_process(UniqueProcess())

async def test_processes_raising_the_process_unregistered_get_unregistered():
    h = Hades()
    p = UniqueProcess()
    h.register_process(p)
    p.add_event(ProcessUnregistered(t=1))
    await h.run()
    assert [type(p) for p in h._processes] == [HadesInternalProcess]

class E1(Event):
    pass
class E2(Event):
    pass

async def test_no_ack_cache_does_not_call_processes_with_events_they_have_no_acked():
    hades = Hades(use_no_ack_cache=True)

    ack_count = 0
    no_ack_count = 0

 

    class SometimesAck(Process):
        def __init__(self, ack_two: bool) -> None:
            self.ack_two = ack_two
            super().__init__()
        async def notify(self, event: Event):
            match event:
                case E1():
                    nonlocal ack_count 
                    ack_count += 1
                    return NotificationResponse.ACK
                case E2():
                    nonlocal no_ack_count
                    no_ack_count += 1
                    return NotificationResponse.ACK if self.ack_two else NotificationResponse.NO_ACK
            return NotificationResponse.NO_ACK

    sometimes_ack_one = SometimesAck(False)
    sometimes_ack_two = SometimesAck(True)
    unique = UniqueProcess()

    hades.register_process(unique)
    hades.register_process(sometimes_ack_one)
    hades.register_process(sometimes_ack_two)

    unique.add_event(E1(t=1))
    unique.add_event(E1(t=2))

    unique.add_event(E2(t=3))
    unique.add_event(E2(t=4))

    await hades.run()
    assert ack_count == 4
    assert no_ack_count == 3



async def test_exception_handling(caplog):
    caplog.set_level(logging.ERROR)
    h = Hades()

    class Raiser(Process):
        async def notify(self, event: Event):
            match event:
                case E1():
                    raise ValueError
                case E2():
                    raise AttributeError
            return NotificationResponse.NO_ACK
    
    h = Hades()
   

    h.register_process(Raiser())
    h.add_event(UniqueProcess(), E1(t=1))
    h.add_event(UniqueProcess(), E2(t=1))
    with pytest.raises(AttributeError):
        await h.run()
    assert "raise ValueError" in caplog.text # we get tracebacks for non raised exceptions



async def test_process_not_returning_notification_response_errors():
    class BadProcess(Process):
        async def notify(self, event: Event):
            match event:
                case SimulationStarted():
                    return NotificationResponse.ACK
            return True
    hades = Hades()
    hades.register_process(BadProcess())
    hades.add_event(UniqueProcess(), E1(t=1))
    hades.add_event(UniqueProcess(), E2(t=1))
    with pytest.raises(TypeError):
        await hades.run()



async def test_runs_till_events_exhausted():
    hades = Hades()
    hades.register_process(UniqueProcess())
    hades.add_event(UniqueProcess(), E1(t=10))
    hades.add_event(UniqueProcess(), E2(t=1000))
    await hades.run()
    assert hades.t == 1000
    assert len(hades.event_history) == 3

async def test_runs_till_until_param():
    hades = Hades(record_results=True)
    hades.register_process(UniqueProcess())
    hades.add_event(UniqueProcess(), E1(t=10))
    hades.add_event(UniqueProcess(), E2(t=1000))
    await hades.run(until=500)
    assert hades.t == 1000
    assert len(hades.event_history) == 2
