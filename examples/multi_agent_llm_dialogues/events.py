
from pydantic import BaseModel

from hades import Event


class CharacterAction(BaseModel):
    location: str
    action_description: str

    class Config: 
        frozen = True


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

