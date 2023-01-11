#!/usr/bin/env python3
"""Actions module."""

import os
import sys

sys.path.append("lib")

from charms.layer.basic import activate_venv  # NOQA E402

activate_venv()

from charmhelpers.core.hookenv import action_fail  # NOQA E402
from lib_cron import CronHelper  # NOQA E402
from lib_logrotate import LogrotateHelper  # NOQA E402

logrotate = LogrotateHelper()
cron = CronHelper()


def update_logrotate_files(args):
    """Update the logrotate files."""
    logrotate.read_config()
    logrotate.modify_configs()


def update_cronjob(args):
    """Update the cronjob file."""
    cron.read_config()
    cron.install_cronjob()


ACTIONS = {
    "update-cronjob": update_cronjob,
    "update-logrotate-files": update_logrotate_files,
}


def main(args):
    """Run assigned action."""
    action_name = os.path.basename(args[0])
    try:
        action = ACTIONS[action_name]
    except KeyError:
        return "Action {} undefined".format(action_name)
    else:
        try:
            action(args)
        except Exception as e:
            action_fail(str(e))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
