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
