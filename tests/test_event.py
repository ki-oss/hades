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

import pytest

from hades import Event


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
