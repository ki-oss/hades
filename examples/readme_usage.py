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
