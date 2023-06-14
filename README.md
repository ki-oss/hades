
<p align="center">
    
<img src="./docs/img/hades.png">
    
</p>
<p align="center">
<img src="https://img.shields.io/badge/version-1.0.0-blue" alt="version">
<img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="version">

</p>
<p align="center">
    <b>HADES</b> <i>(HADES Asynchronous Discrete-Event Simulation)</i> is a small, user friendly framework for creating simulations in python!
</p>

## Features:
* 🎲🤖 **Supports both Agent Based and Process Based models** - how you model the entities in your simulation is up to you!
* ⚡ **Async execution within a time-step** - designed for working IO-bound workloads over the network (e.g. LLM APIs, db lookups, etc)
* 📈 **Visualisation** - `websockets` support to for building a custom frontend for your sim, `matplotlib` in a Jupyter notepad or simply outputting a `mermaid` diagram
* 🏷️ **Pydantic style immutable events** - give type hints and enforcement, making it clear what an event will contain
* 📦 **Encapsulated simulated processes** - processes or agents are encapsulated, keeping state manageable and making it possible to swap processes in and out
* 😊 **User friendly** - pattern matching on pydantic based events makes for an intuitive way to build simulations, while the separation of state helps avoid potential footguns!

## Installation
```shell
pip install hades-framework
```

## Usage
Using the Hades Framework is as simple as creating your custom `Process`es and `Event`s, registering them in the simulation, and letting Hades take care of the rest.

Here are some of the fun things you might do with it:

* [Boids and Websockets](https://github.io/ki-oss/hades/examples/boids) - The classic Boids simulation with canvas and d3.js visualisation via websockets.
    ![boids example](./docs/img/boids.gif)
* [Multi Agent LLM Storytelling](https://github.io/ki-oss/hades/examples/multi) -  Retelling the Odyssey with LLMs - demonstrates the highly IO bound stuff hades is good at. Some output:
    >   "He remembered the sea nymph who had helped him before and realized that having allies like her was crucial to his success. 
        He also continued to use his technological knowledge to stay ahead of Poseidon's wrath, utilizing his drone and sonar to navigate the waters safely."
* [Battery charing station](https://github.io/ki-oss/hades/examples/battery-charging-station) - to help compare what building a simulation looks with `simpy` vs `hades`

Here is a very simple example where we simulate Zeus sending lightning bolts and Poseidon creating storms, both potentially affecting the life of Odysseus:

```python
import asyncio
from enum import Enum

from hades import Event, Hades, NotificationResponse, Process, RandomProcess, SimulationStarted

# Let's define our Events


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


class AthenaIntervened(Event):
    target_id: str


# And now define our Processes


class Zeus(Process):
    async def notify(self, event: Event):
        match event:
            case SimulationStarted(t=t):
                for i in range(0, 100, 25):
                    self.add_event(LightningBoltThrown(t=t + i + 2, target_id="Odysseus"))
                return NotificationResponse.ACK
        return NotificationResponse.NO_ACK


class Poseidon(Process):
    async def notify(self, event: Event):
        match event:
            case SimulationStarted(t=t):
                for i in range(0, 100, 5):
                    self.add_event(StormCreated(t=t + i + 2, target_id="Odysseus"))
                return NotificationResponse.ACK
        return NotificationResponse.NO_ACK


class GoddessAthena(RandomProcess):
    async def notify(self, event: Event):
        match event:
            case SimulationStarted(t=t):
                self.add_event(AthenaIntervened(t=t + 3, target_id="Odysseus"))
                return NotificationResponse.ACK
            case OdysseusDied(t=t):
                if self.random.random() > 0.5:
                    self.add_event(AthenaIntervened(t=t, target_id="Odysseus"))
                else:
                    print("athena was too late to save odysseus")
                return NotificationResponse.ACK
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
        print(f"odysseus' health dropped to {self._health}")
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
            case AthenaIntervened(t=t, target_id=target_id):
                print("but athena intervened saving and healing odysseus to 100")
                self._health = 100
                self.status = HeroLifeCycleStage.SAFE
                return NotificationResponse.ACK
        return NotificationResponse.NO_ACK


# Finally lets compose them to build the simulation


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

To extend this, for example, we could have `Zeus` reacting to `AthenaIntervened` events etc by trying again soon after, or adding some process which leads to `Odysseus` provoking the gods to strike rather than it being at intervals.

## Contribution
We'd love for you to contribute to the Hades Framework! Please check out our [contribution guidelines](./CONTRIBUTING.md) for more details.

## Roadmap

* Support for neo4j visualisation and inspection
* Typescript code generation based on pydantic event models to better support building custom frontends via `HadesWS`
* Support for meta configuration and parametrisations over multiple runs to enable montecarlo style simulations


## Acknowledgements

* [Keith Kam](https://github.com/keith-acn) - contributed performance improvements and tracking of causation events
* [Georgios Xanthos](https://www.instagram.com/weirdink/?hl=en) - contributed the wonderful logo!
* [Zhe Feng](https://github.com/zhe-ki) - review and testing
* [Sedar Olmez](https://github.com/SedarOlmez94) and [Akhil Ahmed](https://github.com/akhila819-ki) - usage and testing through academic research
