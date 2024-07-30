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

from pydantic import BaseModel, ConfigDict

from hades import Event


class CharacterAction(BaseModel):
    location: str
    action_description: str
    model_config = ConfigDict(frozen=True)


class StoryUnfolded(Event):
    chapter: str

    def __str__(self) -> str:
        return f"Day {self.t}: {self.chapter}"


class CharacterActed(Event):
    action: str
    character_name: str

    def __str__(self) -> str:
        return f"""
        Character: {self.character_name}
        Day: {self.t}
        Action: {self.action}
        """


class SynthesisedEventsOfDay(Event):
    day: int
