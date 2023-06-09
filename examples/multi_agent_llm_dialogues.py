import asyncio
import datetime
import enum
import logging
import os

import httpx
import openai
from gpt_json import GPTJSON, GPTMessage, GPTMessageRole, GPTModelVersion
from pydantic import BaseModel, Field
from openai.error import RateLimitError, APIError, Timeout

from hades import Event, Hades, Process
from hades.core.event import Event, SimulationStarted
from hades.core.process import NotificationResponse
from hades.time import datetime_to_step, step_to_date
import feedparser
from dataclasses import asdict

logger = logging.getLogger(__name__)
MOUNT_OLYMPUS = "mount olympus"


greek_gods = {
    "Zeus": "King of the gods and ruler of Mount Olympus",
    "Hera": "Goddess of marriage and queen of the gods",
    "Poseidon": "God of the sea, earthquakes, and horses",
    "Demeter": "Goddess of agriculture and the harvest",
    "Ares": "God of war and violence",
    "Athena": "Goddess of wisdom, courage, and strategic warfare",
    "Apollo": "God of light, music, and healing",
    "Artemis": "Goddess of the hunt, the moon, and childbirth",
    "Hermes": "God of travel, trade, and messenger of the gods",
    "Aphrodite": "Goddess of love, beauty, and desire",
    "Hephaestus": "God of fire, blacksmiths, and craftsmen",
    "Dionysus": "God of wine, celebration, and ecstasy",
    "Hades": "God of the underworld and ruler of the dead",
    "Persephone": "Goddess of the underworld and queen of the dead",
    "Hestia": "Goddess of the hearth, home, and family",
    "Eros": "God of love and attraction",
    "Pan": "God of the wild, shepherds, and flocks",
    "Hypnos": "God of sleep",
}

API_KEY = os.environ["OPENAI_API_KEY"]

class GodCommand(BaseModel):
    command: str | None
    reason: str | None
    argument: str | None
    argument_name: str | None
    command_description: str | None


    class Config:
        frozen = True

class OdysseusAction(BaseModel):
    location: str
    action_description: str

    class Config: 
        frozen = True



class OdysseusActed(Event):
    action: OdysseusAction
    def __str__(self) -> str:
        return f"""
        Day: {self.t}
        Location: {self.action.location}
        Odysseus' Action: {self.action.action_description}
        """
    
class OdysseusPlanned(Event):
    pass

class GodInvokedCommand(Event):
    god_name: str
    command: GodCommand

    def __str__(self) -> str:
        return f"""
        Day: {self.t}
        God: {self.god_name}
        Command: '{self.command.command} ({self.command.command_description})' with argument {self.command.argument_name}='{self.command.argument}'
        """

class SynthesisedEventsOfDay(Event):
    day: int

async def get_plaintext_response(messages: list[GPTMessage]) -> str:
    tries = 7
    while tries:
        try:
            plaintext_response = await openai.ChatCompletion.acreate(api_key=API_KEY, model=GPTModelVersion.GPT_3_5, 
                messages=[asdict(message) for message in messages]
            )
            break
        except (RateLimitError, APIError, Timeout):
            await asyncio.sleep((8 - tries)**2)
            tries -=1
    else:
        raise RateLimitError("getting rate limited")
        
    return plaintext_response.choices[0].message.content


god_command = GPTJSON[GodCommand](API_KEY, model=GPTModelVersion.GPT_3_5, openai_max_retries=10)
odysseus_action_maker = GPTJSON[OdysseusAction](API_KEY, model=GPTModelVersion.GPT_3_5, openai_max_retries=10)

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
            case SynthesisedEventsOfDay(day=day):                
                events_of_day = "\n".join([str(e) for e in self._events_of_day[day]])
                story_of_day = await get_plaintext_response(
                    messages=[
                        GPTMessage(
                            role=GPTMessageRole.SYSTEM,
                            content=(f"""
                            You are the writer Homer chronicling the adventures of a greek hero Odysseus. Here is your story so far.
                            ---
                            {self.story_so_far[-2000:]}
                            ---
                            You will be informed by the user of the events of the current day.

                            You will combine these into the story of Day {day}

                            Example
                            User: Events: ```Day: 0
                            Location: Troy
                            Odysseus' Action: Odyssues is stuck on troy because Poseidon won't allow him home
                            ```
                            Assistant:  As the morning sun rose on Troy, the great hero Odysseus sat frustrated and stuck. He longed to return to his home, his wife and his son, but Poseidon had cursed him, preventing his journey home.
                            Odysseus had tried every trick in his book to appease the sea god, but to no avail. And so he sat, day after day, trying to find any solution to his problem.

                            
                            """),
                        ),
                        GPTMessage(
                            role=GPTMessageRole.USER,
                            content=f"Events ```{events_of_day}```",
                        )
                    ]
                )
                self._story_of_day[day] = story_of_day
                print(f"story of day {day} is: {story_of_day}")
                return NotificationResponse.ACK
                


            case GodInvokedCommand() | OdysseusActed() as e:
                try:
                    self._events_of_day[e.t].append(e)
                except KeyError: 
                    self._events_of_day[e.t] = [e]
                    self.add_event(SynthesisedEventsOfDay(t=e.t+1, day=e.t))
                
                return NotificationResponse.ACK
        return NotificationResponse.NO_ACK
                
class Odysseus(Process):
    def __init__(self) -> None:
        super().__init__()
        self._action_history = []

    async def notify(self, event: Event):
        match event:
            case SimulationStarted(t=t):
                self.add_event(OdysseusActed(t=t, action=OdysseusAction(
                    location="Troy",
                    action_description="Odyssues is stuck on troy because Poseidon won't allow him home"
                )))
            case GodInvokedCommand() as e:
                recent_affairs = '\n'.join(self._action_history[-5:])
                response, _ = await odysseus_action_maker.run(
                    messages=[
                        GPTMessage(
                            role=GPTMessageRole.SYSTEM,
                            content=f"""
                            You are the hero Odysseus.
                            You have the history and motivations of Odysseus at the start of the Odyssey plus the following events 
                            ---
                            {recent_affairs}
                            ---

                            You will be informed of the actions of a god and will react accordingly if they affect you otherwise
                            continue with your plans.

                            Reply according to the following JSON schema:\n ```{{json_schema}}```

                            Example
                            User: Zeus executed command 'lighting (hit target with lighting bolt)' with argument target='Odysseus' home'
                            Assistant: {{{{
                                "action_description": "Flee home, narrowly avoiding the lighting bolts",
                                "location": "Odysseus' home"
                            }}}}
                            """,
                        ),
                        GPTMessage(
                            role=GPTMessageRole.USER,
                            content=str(e),
                        )
                    ]
                )
                if response:
                    event = OdysseusActed(t=e.t, action=response)
                    self.add_event(event)
                    logger.debug(str(event))
                    self._action_history.append(str(response))
                
                return NotificationResponse.ACK
        return NotificationResponse.NO_ACK

class GreekGod(Process):
    def __init__(self, name: str) -> None:
        self._name = name
        self._history = []
        self._commands = None
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
                commands = await get_plaintext_response(messages=[GPTMessage(
                        role=GPTMessageRole.SYSTEM,
                        content=f""""
                        You are designing a game involving greek gods who will hear about events relating to the life of
                        Odysseus and react to them.

                        You need to define a list of commands which the Greek God the user defines may have available to them to 
                        affect the world of business in a way consistent with their character, using your existing knowledge of the god the user 
                        mentions.

                        The user will define how many commands the god will have.

                        Every command must have at least 1 argument.

                        Good arguments would be 'target' or 'location'

                        You must respond with a markdown table only, including the following headers:
                        | Command | Arguments | Description |

                        Example 1:
                        User: `Zeus, 1 commands`
                        Assistant: | Command | Arguments | Description |
                        | --- | --- | --- |
                        | lightning | location | Strikes the location with a lighting bolt |

                        Example 2:
                        User: `Poseidon, 2 commands`
                        Assistant: | Command | Arguments | Description |
| --- | --- | --- |
| earthquake | location | causes an earthquake in the location given |
| wave | location | causes an huge wave in the location given |

                        """,
                    ),
                    GPTMessage(
                        role=GPTMessageRole.USER,
                        content=f"{self._name}: 6 commands",
                    )])
    
                print(f"{self._name} Commands:\n{commands}")
                self._commands = commands
                return NotificationResponse.ACK
            case OdysseusActed() as e:
                
                response, _ = await god_command.run(messages=[
                    GPTMessage(
                        role=GPTMessageRole.SYSTEM,
                        content=f""""
                        You are the greek god {self._name}. You have the history and motivations of {self._name} at the 
                        start of the Odyssey plus the following recent history of your own actions and those of Odysseus
                        ---
                        {self.history_message}
                        ---

                        You have the following commands available to you.
                        {self._commands}
                        | deceive | target, method | deceive the target god using the method mentioned |
                        {'' if self._name == 'Athena' else '| null | null | Do nothing |'}

                        The user will provide you with the latest action of Odysseus.

                        {'' if self._name != "Athena" else "As Athena you are Odysseus' protector and will always do something to help or at least not hinder him."}
                        
                        Respond according to the following schema {{json_schema}}
                        
                        Example Commands:
                        | Command | Arguments | Description |
                        | --- | --- | --- |
                        | lightning | location | Strikes the location with a lighting bolt |
                        | thunder-storm | location | Cause a thunder storm at the target location |
                        {'' if self._name == 'Athena' else '| null | null | Do nothing |'}
                        
                        Example:
                        User: ```
                        Day: 10
                        Location: Ithaca
                        Odysseus' Action: Awakens and believes that he has been dropped on a distant land
                        ```
                        Assistant: {{{{
                            "command": null,
                            "argument": null,
                            "reason": "This does not concern me"
                            "argument_name": null,
                            "command_description": null
                        }}}}
                        """,
                    ),
                    GPTMessage(
                        role=GPTMessageRole.USER,
                        content=str(e),
                    )
                ])
                self._history.append(str(e))
                if response and response.command and response.command.lower() not in ("do-nothing", "null"):
                    event = GodInvokedCommand(t=e.t+1, god_name=self._name, command=response)
                    self.add_event(event)
                    logger.debug(str(event))
                    self._history.append(str(event))
                return NotificationResponse.ACK
            case GodInvokedCommand() as e:
                if self._name not in str(e) or self._name == e.god_name:
                    return NotificationResponse.ACK_BUT_IGNORED
                response, _ = await god_command.run(messages=[
                    GPTMessage(
                        role=GPTMessageRole.SYSTEM,
                        content=f""""
                        You are the greek god {self._name}. You have the history and motivations of {self._name} at the 
                        start of the Odyssey plus the following recent history of your own actions and those of Odysseus
                        ---
                        {self.history_message}
                        ---

                        You have the following commands available to you.
                        {self._commands}
                        | do-nothing | location | Do nothing |

                        The user will provide you with another god's action which concerns you.
                        
                        Respond according to the following schema {{json_schema}}
                        
                        Example Commands:
                        | Command | Arguments | Description |
                        | --- | --- | --- |
                        | lightning | location | Strikes the location with a lighting bolt |
                        | thunder-storm | location | Cause a thunder storm at the target location |
                        | null | null | Do nothing |

                        Example 1:
                        User: ```
                        Day: 5
                        God: Hades
                        Command: 'chaos' (cause chaos) with argument location=Athens for the reason to annoy Odysseus
                        Odysseus' Action: Awakens and believes that he has been dropped on a distant land
                        ```
                        Assistant: {{{{
                            "command": null,
                            "argument": null,
                            "reason": "This does not concern me"
                            "argument_name": null,
                            "command_description": null
                        }}}}
                        """,
                    ),
                    GPTMessage(
                        role=GPTMessageRole.USER,
                        content=str(e),
                    )
                ])
                self._history.append(str(e))
                if response and response.command and response.command.lower() not in ("do-nothing", "null"):
                    event = GodInvokedCommand(t=e.t, god_name=self._name, command=response)
                    self.add_event(event)
                    logger.debug(str(event))
                    self._history.append(str(event))
                return NotificationResponse.ACK
            
            
        return NotificationResponse.NO_ACK


async def simulate(log_level: str):
    logging.getLogger().setLevel(log_level)
    logger.setLevel("INFO")
    world = Hades(batch_event_notification_timeout=20 * 60)
    world.register_process(Odysseus())
    homer = Homer()
    world.register_process(homer)
    for name in ["Athena", "Zeus", "Poseidon"]:
        world.register_process(GreekGod(name=name))
    await world.run(until=10)
    print(homer.story_so_far)


if __name__ == "__main__":
    import sys
    asyncio.run(simulate(sys.argv[1]))
