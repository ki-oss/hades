import asyncio

from examples.multi_agent_llm_storytelling.processes import GreekGod, Homer, Odysseus

from hades import Hades


async def simulate():
    world = Hades(batch_event_notification_timeout=20 * 60)
    world.register_process(Odysseus())
    homer = Homer()
    world.register_process(homer)
    for name in ("Athena", "Zeus", "Poseidon", "Helios"):
        world.register_process(GreekGod(name=name))
    await world.run(until=10)


if __name__ == "__main__":
    asyncio.run(simulate())