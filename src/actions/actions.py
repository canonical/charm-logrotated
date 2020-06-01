#!/usr/bin/env ../.venv/bin/python3
"""Actions module."""

import os
import sys


_path = os.path.dirname(os.path.realpath(__file__))
_hooks = os.path.abspath(os.path.join(_path, '../hooks'))
_lib = os.path.abspath(os.path.join(_path, '../lib'))


def _add_path(path):
    if path not in sys.path:
        sys.path.insert(1, path)

_add_path(_hooks)
_add_path(_lib)

from charmhelpers.core.hookenv import action_fail

from lib_cron import CronHelper

from lib_logrotate import LogrotateHelper

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

ACTIONS = {"update-cronjob": update_cronjob, "update-logrotate-files": update_logrotate_files}


def main(args):
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

