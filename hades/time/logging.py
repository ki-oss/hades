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

from hades.core.hades import Hades
from hades.logging import HadesFilter, setup_step_logging
from hades.time.day_steps import step_to_date


class HadesDateFilter(HadesFilter):
    def filter(self, record):
        setattr(record, "world_date", step_to_date(self._hades.t))
        return super().filter(record)


def setup_date_logging(
    hades: Hades,
    fmt: str = "%(levelname)-8s %(name)s:%(lineno)-4d [%(world_date)s] %(message)s",
):
    setup_step_logging(hades, fmt, HadesDateFilter)
