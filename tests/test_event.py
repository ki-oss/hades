from hades import Event
import pytest

def test_event_immutability():
    event = Event(t=0)

    with pytest.raises(Exception):
        event.t = 1

    assert event.t == 0



def test_event_hashable():
    class SomeEvent(Event):
        a: int
        b: str

    my_dict = {}
    e1 = SomeEvent(t=1, a=1, b="hello")
    e2 = SomeEvent(t=1, a=1, b="hello")

    my_dict[e1] = 1
    my_dict[e2] = 2

    assert my_dict[e1] == 2


def test_event_has_class_name_as_name_attr():
    class SomeEvent(Event):
        pass
    assert SomeEvent(t=1).name == "SomeEvent"
