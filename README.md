# Hades Framework

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/License-MIT-blue.svg)

**HADES** _(HADES Asynchronous Discrete-Event Simulation)_ is a small, user friendly framework for creating simulations in python!


* 🎲🤖 **Supports both Agent Based and Process Based models** - how you model the entities in your simulation is up to you!
* ⚡ **Async execution within a time-step** - makes working with distributed systems easy and makes improving simulation performance simple.
* 🏷️ **Pydantic style events** - gives type hints and enforcement, making it easy to see what an event will contain and improving developer experience
* 📦 **Encapsulated simulated processes** - processes or agents are encapsulated, keeping state manageable and processes easy to swap in or out
* 😊 **User friendly** - pattern matching on pydantic based events makes for an intuitive way to build simulations, while the separation of state helps avoid potential footguns!

## Installation
```shell
pip install hades-framework
```

## Usage
Using the Hades Framework is as simple as creating your custom `processes` and `events`, registering them in the simulation, and letting Hades take care of the rest.

A lot of real power of hades comes when you start combining it with processes which have an async element to them. See the other examples in the [documentation](https://github.io/ki-oss/hades) for a better idea of its strengths and weaknesses!

* [Greek Gods talk current events with LLMs (IO bound stuff hades is good at)](https://github.io/ki-oss/hades/examples/boids)
* [The classic Boids simulation (CPU bound stuff hades is less good at)](https://github.io/ki-oss/hades/examples/boids)
* [Battery charing station (simpy shared resources comparison)](https://github.io/ki-oss/hades/examples/battery-charging-station)

Here is a very simple example where we simulate Zeus sending lightning bolts and Poseidon creating storms, both potentially affecting the life of Odysseus:

```python
import asyncio
from enum import Enum

from hades import Event, Hades, NotificationResponse, Process, RandomProcess, SimulationStarted


class HeroLifeCycleStage(Enum):
    SAFE = 1
    IN_DANGER = 2
    DECEASED = 3


class LightningBoltThrown(Event):
    target_id: str


class StormCreated(Event):
    target_id: str

class OdysseusDied(Event):
    pass

class AthenaIntervenes(Event):
    target_id: str

class Zeus(Process):
    async def notify(self, event: Event):
        match event:
            case SimulationStarted(t=t):
                for i in range(0, 100, 25):
                    self.add_event(LightningBoltThrown(t=t+i+2, target_id="Odysseus"))
                return NotificationResponse.ACK
        return NotificationResponse.NO_ACK


class Poseidon(Process):
    async def notify(self, event: Event):
        match event:
            case SimulationStarted(t=t):
                for i in range(0, 100, 5):
                    self.add_event(StormCreated(t=t+i+2, target_id="Odysseus"))
                return NotificationResponse.ACK
        return NotificationResponse.NO_ACK


class GoddessAthena(RandomProcess):
    async def notify(self, event: Event):
        match event:
            case SimulationStarted(t=t):
                self.add_event(AthenaIntervenes(t=t+3, target_id="Odysseus"))
                return NotificationResponse.ACK
            case OdysseusDied(t=t):
                if self.random.random() > 0.5:
                    self.add_event(AthenaIntervenes(t=t, target_id="Odysseus"))
                else:
                    print("athena was too late to save odysseus")
        return NotificationResponse.NO_ACK


class Odysseus(RandomProcess):
    def __init__(self, seed):
        super().__init__(seed)
        self.status = HeroLifeCycleStage.SAFE
        self._health = 100

    @property
    def instance_identifier(self) -> str:
        return "Odysseus"

    def _handle_peril(self, t: int, max_damage: int, source: str):
        self.status = HeroLifeCycleStage.IN_DANGER
        print(f"odysseus is in danger from {source}!")
        lost_hp = round(self.random.random() * max_damage)
        self._health = max(self._health - lost_hp, 0)
        print(f"odysseus's health dropped to {self._health}")
        if self._health == 0:
            print("odysseus died")
            self.status = HeroLifeCycleStage.DECEASED
            self.add_event(OdysseusDied(t=t))

    async def notify(self, event: Event):
        match event:
            case LightningBoltThrown(t=t, target_id=target_id):
                if self.status == HeroLifeCycleStage.DECEASED:
                    return NotificationResponse.ACK_BUT_IGNORED
                self._handle_peril(t, 90, "Zeus' lightning bolt")
                return NotificationResponse.ACK
            case StormCreated(t=t, target_id=target_id):
                if target_id != self.instance_identifier or self.status == HeroLifeCycleStage.DECEASED:
                    return NotificationResponse.ACK_BUT_IGNORED
                self._handle_peril(t, 50, "Poseidon's storm")
                return NotificationResponse.ACK
            case AthenaIntervenes(t=t, target_id=target_id):
                print("but athena intervened saving and healing odysseus to 100")
                self._health = 100
                self.status = HeroLifeCycleStage.SAFE
        return NotificationResponse.NO_ACK


async def odyssey():
    world = Hades()
    world.register_process(Zeus())
    world.register_process(Poseidon())
    world.register_process(Odysseus("pomegranate"))
    world.register_process(GoddessAthena("pomegranate"))

    await world.run()


if __name__ == "__main__":
    asyncio.run(odyssey())
```

You might already think how you might be able to extend this - having additional 


## Contribution
We'd love for you to contribute to the Hades Framework! Please check out our [contribution guidelines](./CONTRIBUTING.md) for more details.

