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

import pytest

from hades import Hades
from hades.time import QuarterStartScheduler, YearStartScheduler
from hades.visualisation.networkx import to_digraph, write_mermaid


@pytest.fixture
async def simple_sim():
    hades = Hades()
    hades.register_process(YearStartScheduler(start_year=2021))
    hades.register_process(QuarterStartScheduler())

    await hades.run()
    return hades


async def test_hades_process_events_to_digraph_for_simple_sim(simple_sim):
    digraph = to_digraph(simple_sim)
    expected_nodes = (
        "HadesInternalProcess - 7970269937446031133269215595648805179",
        "YearStartScheduler - 332231294394531790607923355838092946842",
        "QuarterStartScheduler - 7836064115094481643618470001379502846",
    )
    expected_edges = (
        (
            "HadesInternalProcess - 7970269937446031133269215595648805179",
            "YearStartScheduler - 332231294394531790607923355838092946842",
            0,
        ),
        (
            "YearStartScheduler - 332231294394531790607923355838092946842",
            "QuarterStartScheduler - 7836064115094481643618470001379502846",
            0,
        ),
    )
    assert tuple(digraph.nodes) == expected_nodes
    assert tuple(digraph.edges) == expected_edges


def test_digraph_to_mermaid_for_simple_sim(simple_sim):
    assert (
        write_mermaid(to_digraph(simple_sim))
        == """graph LR
HadesInternalProcess-7970269937446031133269215595648805179(HadesInternalProcess - 7970269937446031133269215595648805179) -- SimulationStarted --> YearStartScheduler-332231294394531790607923355838092946842(YearStartScheduler - 332231294394531790607923355838092946842)
YearStartScheduler-332231294394531790607923355838092946842(YearStartScheduler - 332231294394531790607923355838092946842) -- YearStarted --> QuarterStartScheduler-7836064115094481643618470001379502846(QuarterStartScheduler - 7836064115094481643618470001379502846)"""
    )
