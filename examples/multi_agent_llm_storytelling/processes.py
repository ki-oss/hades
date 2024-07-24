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

from examples.multi_agent_llm_storytelling.models import GPTMessage

from hades import Event, Process
from hades.core.event import Event, SimulationEnded, SimulationStarted
from hades.core.process import NotificationResponse

from .events import CharacterActed, StoryUnfolded, SynthesisedEventsOfDay
from .prompts import god_prompt, homer_prompt, odysseus_prompt
from .utilities import plaintext_chat_response


class Homer(Process):
    def __init__(self) -> None:
        self._story_of_day = {}
        self._events_of_day = {}
        super().__init__()

    @property
    def story_so_far(self):
        story_so_far = ""
        for story_day, story in self._story_of_day.items():
            story_so_far += f"\nDay {story_day}: {story}\n"
        return story_so_far

    async def notify(self, event: Event):
        match event:
            case SynthesisedEventsOfDay(day=day, t=t):
                events_of_day = "\n".join([str(e) for e in self._events_of_day[day]])
                story_of_day = await plaintext_chat_response(
                    messages=[
                        GPTMessage(
                            role=GPTMessageRole.SYSTEM,
                            content=homer_prompt.format(story_so_far=self.story_so_far[-2000:], day=day),
                        ),
                        GPTMessage(
                            role=GPTMessageRole.USER,
                            content=f"Events ```{events_of_day}```",
                        ),
                    ]
                )
                self.add_event(StoryUnfolded(t=t, chapter=story_of_day))
                self._story_of_day[day] = story_of_day
                print(f"Day {day}: {story_of_day}")
                return NotificationResponse.ACK
            case CharacterActed() as e:
                # collect all the events of the day to synthesise the next day
                try:
                    self._events_of_day[e.t].append(e)
                except KeyError:
                    self._events_of_day[e.t] = [e]
                    self.add_event(SynthesisedEventsOfDay(t=e.t + 1, day=e.t))
                return NotificationResponse.ACK
            case SimulationEnded():
                print(self.story_so_far)
                return NotificationResponse.ACK
        return NotificationResponse.NO_ACK


class Odysseus(Process):
    def __init__(self) -> None:
        super().__init__()
        self._name = "Odysseus"
        self._action_history = []

    async def notify(self, event: Event):
        match event:
            case SimulationStarted(t=t):
                self.add_event(
                    CharacterActed(
                        t=t,
                        character_name=self._name,
                        action=(
                            "Odyssues crys out in frustration at being stuck in Troy because Poseidon won't allow him"
                            " home"
                        ),
                    )
                )
            case StoryUnfolded() as e:
                recent_affairs = "\n".join(self._action_history[-5:])
                response = await plaintext_chat_response(
                    messages=[
                        GPTMessage(
                            role=GPTMessageRole.SYSTEM,
                            content=odysseus_prompt.format(recent_affairs=recent_affairs, day=e.t),
                        ),
                        GPTMessage(
                            role=GPTMessageRole.USER,
                            content=str(e),
                        ),
                    ]
                )
                self._action_history.append(str(e))
                if response:
                    event = CharacterActed(t=e.t, action=response, character_name=self._name)
                    self.add_event(event)
                    self._action_history.append(str(response))

                return NotificationResponse.ACK
        return NotificationResponse.NO_ACK


class GreekGod(Process):
    def __init__(self, name: str) -> None:
        self._name = name
        self._history = []
        self._motives = None
        super().__init__()

    @property
    def history_message(self):
        if self._history:
            return " You have the following recent history: " + "\n".join(self._history[-5:])
        else:
            return ""

    async def notify(self, event: Event):
        match event:
            case SimulationStarted():
                motives = await plaintext_chat_response(
                    messages=[
                        GPTMessage(
                            role=GPTMessageRole.USER,
                            content=f""""
                        Describe the core motives of {self._name} at the start of the Odyssey in less than 200 words.""",
                        )
                    ]
                )
                print(f"{self._name} Motivations:\n{motives}")
                self._motives = motives
                return NotificationResponse.ACK
            case StoryUnfolded() as e:
                response = await plaintext_chat_response(
                    messages=[
                        GPTMessage(
                            role=GPTMessageRole.SYSTEM,
                            content=god_prompt.format(
                                god_name=self._name, motives=self._motives, day=e.t, history=self.history_message
                            ),
                        ),
                        GPTMessage(
                            role=GPTMessageRole.USER,
                            content=e.chapter,
                        ),
                    ]
                )
                self._history.append(str(e))
                if response:
                    event = CharacterActed(t=e.t, action=response, character_name=self._name)
                    self.add_event(event)
                return NotificationResponse.ACK
        return NotificationResponse.NO_ACK
