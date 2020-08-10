#!/usr/bin/env python3
"""Actions module."""

import os
import sys

from charmhelpers.core import hookenv

from lib_cron import CronHelper

from lib_logrotate import LogrotateHelper

sys.path.insert(0, os.path.join(os.environ["CHARM_DIR"], "lib"))

hooks = hookenv.Hooks()
logrotate = LogrotateHelper()
cron = CronHelper()


@hooks.hook("update-logrotate-files")
def update_logrotate_files():
    """Update the logrotate files."""
    logrotate.read_config()
    logrotate.modify_configs()


@hooks.hook("update-cronjob")
def update_cronjob():
    """Update the cronjob file."""
    cron.read_config()
    cron.install_cronjob()


if __name__ == "__main__":
    """Main function."""
    hooks.execute(sys.argv)
