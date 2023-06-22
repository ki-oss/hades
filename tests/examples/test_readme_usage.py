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

from examples.readme_usage import odyssey


async def test_gives_expected_logs(capsys):
    await odyssey()
    assert capsys.readouterr().out == """odysseus is in danger from Zeus' lightning bolt!
odysseus' health dropped to 77
odysseus is in danger from Poseidon's storm!
odysseus' health dropped to 63
but athena intervened saving and healing odysseus to 100
odysseus is in danger from Poseidon's storm!
odysseus' health dropped to 78
odysseus is in danger from Poseidon's storm!
odysseus' health dropped to 65
odysseus is in danger from Poseidon's storm!
odysseus' health dropped to 42
odysseus is in danger from Poseidon's storm!
odysseus' health dropped to 42
odysseus is in danger from Zeus' lightning bolt!
odysseus' health dropped to 30
odysseus is in danger from Poseidon's storm!
odysseus' health dropped to 0
odysseus died
athena was too late to save odysseus
"""
