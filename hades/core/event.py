"""
Events should use a consistent tense. Here past is used

It will often be the case that events will need to contain identifying information for processes to identify which entity it relates 
to within their internal state. In addition it will often be necessary to pass around data.

Another thing which may be useful is some kind of audience identifier, which can help processes distinguish quickly whether to 
do anything with a give event.

Suggested way to structure this is as follows:

Suppose we have two Event kinds relating to frogs:
* `FrogSpawned`
* `FrogTransformed`


```python
class FrogLifeCycleStage(Enum):
    SPAWN = 1
    TADPOLE = 2
    FROGLET = 3
    FROG = 4

class FrogSpawned(Event):
    frog_id: str
    audience_pond_id: str

    initial_stage: FrogLifeCycleStage
    frog_genetic_data: GeneticData

class FrogTransformed(Event):
    frog_id: str
    # we dont need the audience here because we might well assume that a frog will spend its whole life in the start pond
    # we also dont need the genetic data because 
    transformed_to: FrogLifeCycleStage
```

This ensures that processes can cleanly identify whether the event relates to an entity they are interested in and makes a distinction
between data (which may be quite sizeable) isn't being unnecessarily passed around.
"""
from pydantic import BaseModel


class Event(BaseModel):
    """base event - event occurrence step t must be included. It is immutable and hashable"""

    t: int

    @property
    def name(self):
        return self.__class__.__name__
    
    # def __hash__(self) -> int:
    #     return hash(str(self.dict()))
    class Config:
        frozen = True

class SimulationStarted(Event):
    """special event issued by hades to kick off the sim"""

    t: int = 0


class ProcessUnregistered(Event):
    """
    special event for unregistered the process who sent this event.
    it is unique in that it will be consumed by hades and not broadcast to other processes.
    """
