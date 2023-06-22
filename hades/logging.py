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
from typing import Type

from hades.core.hades import Hades


class HadesFilter(logging.Filter):
    def __init__(self, hades: Hades) -> None:
        self._hades = hades
        super().__init__()

    def filter(self, record):
        setattr(record, "step", self._hades.t)
        return True


def setup_step_logging(
    hades: Hades,
    fmt: str = "%(levelname)-8s %(name)s:%(lineno)-4d [t=%(step)d] %(message)s",
    filter_cls: Type[HadesFilter] = HadesFilter,
):
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(filter_cls(hades))
        handler.setFormatter(logging.Formatter(fmt))
