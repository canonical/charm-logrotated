from lib_logrotate import LogrotateHelper
from lib_cron import CronHelper
from charmhelpers.core import hookenv
from charms.reactive import set_flag, when, when_not

logrotate = LogrotateHelper()
cron = CronHelper()

@when_not('logrotate.installed')
def install_logrotate():
    dump_config_to_disk();
    logrotate.read_config()
    cron.read_config()
    logrotate.modify_configs()
    hookenv.status_set('active', 'Unit is ready.')
    set_flag('logrotate.installed')
    cron.install_cronjob();

@when('config.changed')
def config_changed():
    dump_config_to_disk()
    cron.read_config()
    logrotate.read_config()
    hookenv.status_set('maintenance', 'Modifying configs.')
    logrotate.modify_configs()
    hookenv.status_set('active', 'Unit is ready.')
    cron.install_cronjob();

def dump_config_to_disk():
    cronjob_enabled = hookenv.config('logrotate-cronjob')
    cronjob_frequency = hookenv.config('logrotate-cronjob-frequency')
    logrotate_retention = hookenv.config('logrotate-retention')
    with open('/etc/logrotate_cronjob_config', 'w+') as cronjob_config_file:
       cronjob_config_file.write(str(cronjob_enabled) + '\n')
       cronjob_config_file.write(str(cronjob_frequency) + '\n')
       cronjob_config_file.write(str(logrotate_retention) + '\n')
