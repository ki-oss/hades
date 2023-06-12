
import logging

from hades import Hades
from hades.time import YearStartScheduler
from hades.time.logging import setup_date_logging


async def test_logging_hades(caplog, capsys):
    caplog.set_level(logging.DEBUG)
    hades = Hades()
    setup_date_logging(hades, fmt="%(levelname)-8s %(name)s [%(world_date)s] %(message)s") # drop line number to make less sensitive to code changes
    hades.register_process(YearStartScheduler(start_year=2023, look_ahead_years=2))
    await hades.run()
    assert caplog.text == """INFO     hades.core.hades [0001-01-01] registered process: YearStartScheduler, instance: 332231294394531790607923355838092946842
INFO     hades.core.hades [0001-01-01] registered process: HadesInternalProcess, instance: 7836064115094481643618470001379502846
DEBUG    hades.core.hades [0001-01-01] adding SimulationStarted from process: HadesInternalProcess, instance: 7836064115094481643618470001379502846 to queue
DEBUG    hades.core.hades [0001-01-01] getting events for next timestamp
DEBUG    hades.core.hades [0001-01-01] added event=SimulationStarted(t=0) to next events batch
DEBUG    hades.core.hades [0001-01-01] got 1 events at time 0
DEBUG    hades.time.process [0001-01-01] adding look ahead YearStarted events between 2023 and 2025 due to SimulationStarted(t=0)
DEBUG    hades.core.hades [0001-01-01] adding YearStarted from process: YearStartScheduler, instance: 332231294394531790607923355838092946842 to queue
DEBUG    hades.core.hades [0001-01-01] adding YearStarted from process: YearStartScheduler, instance: 332231294394531790607923355838092946842 to queue
DEBUG    hades.core.hades [0001-01-01] completed task notify process: YearStartScheduler, instance: 332231294394531790607923355838092946842 of t=0 from process: HadesInternalProcess, instance: 7836064115094481643618470001379502846 with result NotificationResponse.ACK
DEBUG    hades.core.hades [0001-01-01] completed task notify process: HadesInternalProcess, instance: 7836064115094481643618470001379502846 of t=0 from process: HadesInternalProcess, instance: 7836064115094481643618470001379502846 with result NotificationResponse.NO_ACK
DEBUG    hades.core.hades [0001-01-01] getting events for next timestamp
DEBUG    hades.core.hades [0001-01-01] time moved to 738520
DEBUG    hades.core.hades [2023-01-01] added event=YearStarted(t=738520) to next events batch
DEBUG    hades.core.hades [2023-01-01] got 1 events at time 738520
DEBUG    hades.core.hades [2023-01-01] completed task notify process: YearStartScheduler, instance: 332231294394531790607923355838092946842 of t=738520 from process: YearStartScheduler, instance: 332231294394531790607923355838092946842 with result NotificationResponse.ACK_BUT_IGNORED
DEBUG    hades.core.hades [2023-01-01] completed task notify process: HadesInternalProcess, instance: 7836064115094481643618470001379502846 of t=738520 from process: YearStartScheduler, instance: 332231294394531790607923355838092946842 with result NotificationResponse.NO_ACK
DEBUG    hades.core.hades [2023-01-01] getting events for next timestamp
DEBUG    hades.core.hades [2023-01-01] time moved to 738885
DEBUG    hades.core.hades [2024-01-01] added event=YearStarted(t=738885) to next events batch
DEBUG    hades.core.hades [2024-01-01] got 1 events at time 738885
DEBUG    hades.core.hades [2024-01-01] completed task notify process: YearStartScheduler, instance: 332231294394531790607923355838092946842 of t=738885 from process: YearStartScheduler, instance: 332231294394531790607923355838092946842 with result NotificationResponse.ACK_BUT_IGNORED
DEBUG    hades.core.hades [2024-01-01] completed task notify process: HadesInternalProcess, instance: 7836064115094481643618470001379502846 of t=738885 from process: YearStartScheduler, instance: 332231294394531790607923355838092946842 with result NotificationResponse.NO_ACK
DEBUG    hades.core.hades [2024-01-01] getting events for next timestamp
DEBUG    hades.core.hades [2024-01-01] got 0 events at time 738885
INFO     hades.core.hades [2024-01-01] ending run as we have exhausted the queue of events!
"""
