"""Reactive charm hooks."""
from charmhelpers.core import hookenv

from charms.reactive import set_flag, when, when_not

from lib_cron import CronHelper

from lib_logrotate import LogrotateHelper


hooks = hookenv.Hooks()
logrotate = LogrotateHelper()
cron = CronHelper()


@when_not("logrotate.installed")
def install_logrotate():
    """Install the logrotate charm."""
    try:
        dump_config_to_disk()
        logrotate.read_config()
        cron.read_config()
        logrotate.modify_configs()
        cron.install_cronjob()
    except Exception as ex:
        hookenv.status_set("blocked", str(ex))
    hookenv.status_set("active", "Unit is ready.")
    set_flag("logrotate.installed")


@when("config.changed")
def config_changed():
    """Run when configuration changes."""
    try:
        dump_config_to_disk()
        cron.read_config()
        logrotate.read_config()
        hookenv.status_set("maintenance", "Modifying configs.")
        logrotate.modify_configs()
        cron.install_cronjob()
    except Exception as ex:
        hookenv.status_set("blocked", str(ex))
    hookenv.status_set("active", "Unit is ready.")


def dump_config_to_disk():
    """Dump configurations to disk."""
    cronjob_enabled = hookenv.config("logrotate-cronjob")
    cronjob_frequency = hookenv.config("logrotate-cronjob-frequency")
    logrotate_retention = hookenv.config("logrotate-retention")
    cron_daily_schedule = hookenv.config("update-cron-daily-schedule")
    with open("/etc/logrotate_cronjob_config", "w+") as cronjob_config_file:
        cronjob_config_file.write(str(cronjob_enabled) + "\n")
        cronjob_config_file.write(str(cronjob_frequency) + "\n")
        cronjob_config_file.write(str(logrotate_retention) + "\n")
        cronjob_config_file.write(str(cron_daily_schedule) + "\n")
