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

import logging

from hades import Hades
from hades.logging import setup_step_logging
from hades.time import YearStartScheduler


async def test_process_with_hades_logger_adapter(caplog):
    caplog.set_level(logging.DEBUG)
    hades = Hades()
    setup_step_logging(hades, fmt="%(levelname)-8s %(name)s [t=%(step)d] %(message)s")

    hades.register_process(YearStartScheduler(start_year=2023, look_ahead_years=2))
    await hades.run()
    assert (
        caplog.text
        == """INFO     hades.core.hades [t=0] registered process: YearStartScheduler, instance: 332231294394531790607923355838092946842
INFO     hades.core.hades [t=0] registered process: HadesInternalProcess, instance: 7836064115094481643618470001379502846
DEBUG    hades.core.hades [t=0] adding SimulationStarted from process: HadesInternalProcess, instance: 7836064115094481643618470001379502846 (caused by None) to queue
DEBUG    hades.core.hades [t=0] getting events for next timestamp
DEBUG    hades.core.hades [t=0] added event=SimulationStarted(t=0) to next events batch
DEBUG    hades.core.hades [t=0] got 1 events at time 0
DEBUG    hades.time.process [t=0] adding look ahead YearStarted events between 2023 and 2025 due to SimulationStarted(t=0)
DEBUG    hades.core.hades [t=0] adding YearStarted from process: YearStartScheduler, instance: 332231294394531790607923355838092946842 (caused by None) to queue
DEBUG    hades.core.hades [t=0] adding YearStarted from process: YearStartScheduler, instance: 332231294394531790607923355838092946842 (caused by None) to queue
DEBUG    hades.core.hades [t=0] completed task notify process: YearStartScheduler, instance: 332231294394531790607923355838092946842 of t=0 from process: HadesInternalProcess, instance: 7836064115094481643618470001379502846 with result NotificationResponse.ACK
DEBUG    hades.core.hades [t=0] completed task notify process: HadesInternalProcess, instance: 7836064115094481643618470001379502846 of t=0 from process: HadesInternalProcess, instance: 7836064115094481643618470001379502846 with result NotificationResponse.NO_ACK
DEBUG    hades.core.hades [t=0] getting events for next timestamp
DEBUG    hades.core.hades [t=0] time moved to 738520
DEBUG    hades.core.hades [t=738520] added event=YearStarted(t=738520) to next events batch
DEBUG    hades.core.hades [t=738520] got 1 events at time 738520
DEBUG    hades.core.hades [t=738520] completed task notify process: YearStartScheduler, instance: 332231294394531790607923355838092946842 of t=738520 from process: YearStartScheduler, instance: 332231294394531790607923355838092946842 with result NotificationResponse.ACK_BUT_IGNORED
DEBUG    hades.core.hades [t=738520] completed task notify process: HadesInternalProcess, instance: 7836064115094481643618470001379502846 of t=738520 from process: YearStartScheduler, instance: 332231294394531790607923355838092946842 with result NotificationResponse.NO_ACK
DEBUG    hades.core.hades [t=738520] getting events for next timestamp
DEBUG    hades.core.hades [t=738520] time moved to 738885
DEBUG    hades.core.hades [t=738885] added event=YearStarted(t=738885) to next events batch
DEBUG    hades.core.hades [t=738885] got 1 events at time 738885
DEBUG    hades.core.hades [t=738885] completed task notify process: YearStartScheduler, instance: 332231294394531790607923355838092946842 of t=738885 from process: YearStartScheduler, instance: 332231294394531790607923355838092946842 with result NotificationResponse.ACK_BUT_IGNORED
DEBUG    hades.core.hades [t=738885] completed task notify process: HadesInternalProcess, instance: 7836064115094481643618470001379502846 of t=738885 from process: YearStartScheduler, instance: 332231294394531790607923355838092946842 with result NotificationResponse.NO_ACK
DEBUG    hades.core.hades [t=738885] getting events for next timestamp
DEBUG    hades.core.hades [t=738885] got 0 events at time 738885
INFO     hades.core.hades [t=738885] ending run as we have exhausted the queue of events!
"""
    )
