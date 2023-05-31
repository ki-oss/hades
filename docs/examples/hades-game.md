# Hades Game

A nod to a name sharing game. Kindly contributed by [Zhe](https://github.com/zhe-ki)!


## Code

```python
import asyncio
from typing import List, Tuple
from pydantic import BaseModel
from ki_abv.framework import hades


class Character(BaseModel):
    hp: int
    attack: int

    def got_hit(self, strength: int):
        self.hp = max(self.hp - strength, 0)

    def is_live(self):
        return self.hp > 0


class Hero(Character):
    name: str = "Zagreus"


class Mob(Character):
    name: str = "BoneHydra"


class Smash(hades.Event):
    from_: str
    to: List[str]
    strength: int


class MobVisibleToHero(hades.Event):
    mob_names: List[str]


class HeroVisibleToMob(hades.Event):
    hero_name: str = "Zagreus"


class GameOver(hades.Event):
    reason: str


class MobDied(hades.Event):
    mob_name: str


class NoobPlayer(hades.Process):
    """ """

    def __init__(self, hero: Hero) -> None:
        self.hero = hero
        self.killed_mob = []
        super().__init__()

    async def notify(self, event: hades.Event) -> hades.NotificationResponse:

        match event:
            case GameOver() as gameover:
                raise ValueError(f"gameover because {gameover.reason} at step {gameover.t}")
            case MobDied() as mobdied:
                self.killed_mob.append(mobdied.mob_name)
            case MobVisibleToHero() as visible_mobs:
                # smash the mob after you see the mob
                if len(visible_mobs.mob_names) == 0:
                    raise ValueError("at least one mob should be visible when `MobVisibleToHero` happens")
                live_mobs = [mob_name for mob_name in visible_mobs.mob_names if mob_name not in self.killed_mob]
                if live_mobs:
                    picked = live_mobs[0]
                    smash = Smash(
                        from_=self.hero.name,
                        to=[picked],
                        strength=self.hero.attack,
                        t=visible_mobs.t + 1,
                    )
                    self.add_event(smash)
                return hades.NotificationResponse.ACK
            case Smash() as smash:
                if self.hero.name in smash.to:
                    self.hero.got_hit(strength=smash.strength)
                    print(f"{self.hero.name} got smashed and now has {self.hero.hp} remaining")
                return hades.NotificationResponse.ACK

        if not self.hero.is_live():
            self.add_event(GameOver(reason="hero died", t=event.t + 1))
            print(f"{self.hero.name} died")
        return hades.NotificationResponse.NO_ACK


class NoobMobsAI(hades.Process):
    def __init__(self, mobs: List[Mob]) -> None:
        self.mobs = mobs
        super().__init__()

    async def notify(self, event: hades.Event) -> hades.NotificationResponse:

        match event:
            case GameOver() as gameover:
                raise ValueError(f"gameover because {gameover.reason} at step {gameover.t}")
            case HeroVisibleToMob() as hero_spotted:
                for mob in self.mobs:
                    if mob.is_live():
                        smash = Smash(
                            from_=mob.name,
                            to=[hero_spotted.hero_name],
                            strength=mob.attack,
                            t=hero_spotted.t + 1,
                        )
                        self.add_event(smash)
                        print(f"{mob.name} smashing {smash.to} for {smash.strength} hp at step {smash.t}")
                return hades.NotificationResponse.ACK
            case Smash() as smash:
                for mob in self.mobs:
                    if mob.name in smash.to:
                        mob.got_hit(strength=smash.strength)
                        print(
                            f"{mob.name} smashed by {smash.from_} for {smash.strength} hp at step {smash.t} and now has {mob.hp} hp left"
                        )
                        if not mob.is_live():
                            self.add_event(MobDied(mob_name=mob.name, t=smash.t))
                return hades.NotificationResponse.ACK

        if all([not mob.is_live() for mob in self.mobs]):
            self.add_event(GameOver(reason="all mob died", t=event.t + 1))
            print("all mob died")
        return hades.NotificationResponse.NO_ACK


class Encounter(BaseModel):
    mobs: List[str]


class EncounterGenerator(hades.Process):
    def __init__(self, encounter_steps: List[Tuple[Encounter, int]]) -> None:
        self.encounter_steps = encounter_steps
        super().__init__()

    async def notify(self, event: hades.Event) -> hades.NotificationResponse:
        match event:
            case GameOver() as gameover:
                raise ValueError(f"gameover because {gameover.reason} at step {gameover.t}")
                return hades.NotificationResponse.ACK
            case hades.SimulationStarted() as started:
                for encounter, step in self.encounter_steps:
                    self.add_event(HeroVisibleToMob(t=started.t + step))
                    self.add_event(MobVisibleToHero(mob_names=encounter.mobs, t=started.t + step))
                return hades.NotificationResponse.ACK
        return hades.NotificationResponse.NO_ACK


async def run_sim():
    # change here to see how things go
    underworld = hades.core.hades(random_pomegranate_seed="Come, shades, I don't have all night!")
    player_process = NoobPlayer(Hero(hp=500, attack=15))
    mobs_process = NoobMobsAI(
        mobs=[
            Mob(name="BoneHydra1", hp=50, attack=5),
            Mob(name="BoneHydra2", hp=50, attack=5),
            Mob(name="Bloodless1", hp=100, attack=10),
        ]
    )
    encounters = EncounterGenerator(
        encounter_steps=[
            (Encounter(mobs=["BoneHydra1"]), 1),
            (Encounter(mobs=["BoneHydra1", "BoneHydra2"]), 2),
            (Encounter(mobs=["BoneHydra1", "BoneHydra2"]), 3),
            (Encounter(mobs=["BoneHydra1", "BoneHydra2"]), 5),
            (Encounter(mobs=["BoneHydra1", "BoneHydra2"]), 5),
            (Encounter(mobs=["BoneHydra1", "BoneHydra2"]), 10),
            (Encounter(mobs=["BoneHydra1", "BoneHydra2", "Bloodless1"]), 20),
            (Encounter(mobs=["BoneHydra1", "BoneHydra2", "Bloodless1"]), 21),
            (Encounter(mobs=["BoneHydra1", "BoneHydra2", "Bloodless1"]), 22),
            (Encounter(mobs=["BoneHydra1", "BoneHydra2", "Bloodless1"]), 23),
            (Encounter(mobs=["BoneHydra1", "BoneHydra2", "Bloodless1"]), 24),
            (Encounter(mobs=["BoneHydra1", "BoneHydra2", "Bloodless1"]), 25),
            (Encounter(mobs=["BoneHydra1", "BoneHydra2", "Bloodless1"]), 26),
            (Encounter(mobs=["BoneHydra1", "BoneHydra2", "Bloodless1"]), 27),
            (Encounter(mobs=["BoneHydra1", "BoneHydra2", "Bloodless1"]), 28),
            (Encounter(mobs=["BoneHydra1", "BoneHydra2", "Bloodless1"]), 29),
            (Encounter(mobs=["BoneHydra1", "BoneHydra2", "Bloodless1"]), 30),
        ]
    )
    underworld.register_process(player_process)
    underworld.register_process(mobs_process)
    underworld.register_process(encounters)
    await underworld.run(until=35)


if __name__ == "__main__":
    asyncio.run(run_sim())
```

## Log Output

```
BoneHydra1 smashing ['Zagreus'] for 5 hp at step 2
BoneHydra2 smashing ['Zagreus'] for 5 hp at step 2
Bloodless1 smashing ['Zagreus'] for 10 hp at step 2
Zagreus got smashed and now has 495 remaining
Zagreus got smashed and now has 490 remaining
Zagreus got smashed and now has 480 remaining
BoneHydra1 smashing ['Zagreus'] for 5 hp at step 3
BoneHydra2 smashing ['Zagreus'] for 5 hp at step 3
Bloodless1 smashing ['Zagreus'] for 10 hp at step 3
BoneHydra1 smashed by Zagreus for 15 hp at step 2 and now has 35 hp left
Zagreus got smashed and now has 475 remaining
Zagreus got smashed and now has 470 remaining
Zagreus got smashed and now has 460 remaining
BoneHydra1 smashing ['Zagreus'] for 5 hp at step 4
BoneHydra2 smashing ['Zagreus'] for 5 hp at step 4
Bloodless1 smashing ['Zagreus'] for 10 hp at step 4
BoneHydra1 smashed by Zagreus for 15 hp at step 3 and now has 20 hp left
Zagreus got smashed and now has 455 remaining
Zagreus got smashed and now has 450 remaining
Zagreus got smashed and now has 440 remaining
BoneHydra1 smashed by Zagreus for 15 hp at step 4 and now has 5 hp left
BoneHydra1 smashing ['Zagreus'] for 5 hp at step 6
BoneHydra2 smashing ['Zagreus'] for 5 hp at step 6
Bloodless1 smashing ['Zagreus'] for 10 hp at step 6
BoneHydra1 smashing ['Zagreus'] for 5 hp at step 6
BoneHydra2 smashing ['Zagreus'] for 5 hp at step 6
Bloodless1 smashing ['Zagreus'] for 10 hp at step 6
Zagreus got smashed and now has 435 remaining
Zagreus got smashed and now has 430 remaining
Zagreus got smashed and now has 420 remaining
Zagreus got smashed and now has 415 remaining
Zagreus got smashed and now has 410 remaining
Zagreus got smashed and now has 400 remaining
BoneHydra1 smashed by Zagreus for 15 hp at step 6 and now has 0 hp left
BoneHydra1 smashed by Zagreus for 15 hp at step 6 and now has 0 hp left
BoneHydra2 smashing ['Zagreus'] for 5 hp at step 11
Bloodless1 smashing ['Zagreus'] for 10 hp at step 11
Zagreus got smashed and now has 395 remaining
Zagreus got smashed and now has 385 remaining
BoneHydra2 smashed by Zagreus for 15 hp at step 11 and now has 35 hp left
BoneHydra2 smashing ['Zagreus'] for 5 hp at step 21
Bloodless1 smashing ['Zagreus'] for 10 hp at step 21
Zagreus got smashed and now has 380 remaining
Zagreus got smashed and now has 370 remaining
BoneHydra2 smashing ['Zagreus'] for 5 hp at step 22
Bloodless1 smashing ['Zagreus'] for 10 hp at step 22
BoneHydra2 smashed by Zagreus for 15 hp at step 21 and now has 20 hp left
Zagreus got smashed and now has 365 remaining
Zagreus got smashed and now has 355 remaining
BoneHydra2 smashing ['Zagreus'] for 5 hp at step 23
Bloodless1 smashing ['Zagreus'] for 10 hp at step 23
BoneHydra2 smashed by Zagreus for 15 hp at step 22 and now has 5 hp left
Zagreus got smashed and now has 350 remaining
Zagreus got smashed and now has 340 remaining
BoneHydra2 smashing ['Zagreus'] for 5 hp at step 24
Bloodless1 smashing ['Zagreus'] for 10 hp at step 24
BoneHydra2 smashed by Zagreus for 15 hp at step 23 and now has 0 hp left
Zagreus got smashed and now has 335 remaining
Zagreus got smashed and now has 325 remaining
Bloodless1 smashing ['Zagreus'] for 10 hp at step 25
BoneHydra2 smashed by Zagreus for 15 hp at step 24 and now has 0 hp left
Zagreus got smashed and now has 315 remaining
Bloodless1 smashing ['Zagreus'] for 10 hp at step 26
Bloodless1 smashed by Zagreus for 15 hp at step 25 and now has 85 hp left
Zagreus got smashed and now has 305 remaining
Bloodless1 smashing ['Zagreus'] for 10 hp at step 27
Bloodless1 smashed by Zagreus for 15 hp at step 26 and now has 70 hp left
Zagreus got smashed and now has 295 remaining
Bloodless1 smashing ['Zagreus'] for 10 hp at step 28
Bloodless1 smashed by Zagreus for 15 hp at step 27 and now has 55 hp left
Zagreus got smashed and now has 285 remaining
Bloodless1 smashing ['Zagreus'] for 10 hp at step 29
Bloodless1 smashed by Zagreus for 15 hp at step 28 and now has 40 hp left
Zagreus got smashed and now has 275 remaining
Bloodless1 smashing ['Zagreus'] for 10 hp at step 30
Bloodless1 smashed by Zagreus for 15 hp at step 29 and now has 25 hp left
Zagreus got smashed and now has 265 remaining
Bloodless1 smashing ['Zagreus'] for 10 hp at step 31
Bloodless1 smashed by Zagreus for 15 hp at step 30 and now has 10 hp left
Zagreus got smashed and now has 255 remaining
Bloodless1 smashed by Zagreus for 15 hp at step 31 and now has 0 hp left
all mob died
ERROR    hades.core.hades:192  [0001-02-02] got additional exception (not raised) as part of batch from {"target_process": "NoobMobsAI", "target_process_instance": "4352455120", "event": "GameOver", "event_index": 0}
Traceback (most recent call last):
  File "ki_abv/framework/hades/hades.py", line 190, in run
    raise exc
  File "boids.py", line 94, in notify
    raise ValueError(f"gameover because {gameover.reason} at step {gameover.t}")
ValueError: gameover because all mob died at step 32
ERROR    hades.core.hades:192  [0001-02-02] got additional exception (not raised) as part of batch from {"target_process": "NoobPlayer", "target_process_instance": "4335836112", "event": "GameOver", "event_index": 0}
Traceback (most recent call last):
  File "ki_abv/framework/hades/hades.py", line 190, in run
    raise exc
  File "boids.py", line 60, in notify
    raise ValueError(f"gameover because {gameover.reason} at step {gameover.t}")
ValueError: gameover because all mob died at step 32
Traceback (most recent call last):
  File "boids.py", line 173, in <module>
    asyncio.run(run_sim())
  File "3.11.1/lib/python3.11/asyncio/runners.py", line 190, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "3.11.1/lib/python3.11/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "3.11.1/lib/python3.11/asyncio/base_events.py", line 653, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "boids.py", line 170, in run_sim
    await underworld.run(until=35)
  File "ki_abv/framework/hades/hades.py", line 188, in run
    raise exc
  File "boids.py", line 129, in notify
    raise ValueError(f"gameover because {gameover.reason} at step {gameover.t}")
ValueError: gameover because all mob died at step 32
```
