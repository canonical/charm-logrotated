#!/usr/bin/env python3
#
# Copyright 2016 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

sys.path.insert(0, os.path.join(os.environ['CHARM_DIR'], 'lib'))
from charmhelpers.core import (
    hookenv,
    host,
)

from lib_logrotate import LogrotateHelper
from lib_cron import CronHelper

hooks = hookenv.Hooks()
logrotate = LogrotateHelper()
cron = CronHelper()

@hooks.hook("update-logrotate-files")
def update_logrotate_files():
    logrotate.read_config()
    logrotate.modify_configs()

@hooks.hook("update-cronjob")
def update_cronjob():
    cron.read_config()
    cron.install_cronjob()

if __name__ == "__main__":
    hooks.execute(sys.argv)

