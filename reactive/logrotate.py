from lib_logrotate import LogrotateHelper
from charmhelpers.core import hookenv
from charms.reactive import set_flag, when, when_not

logrotate = LogrotateHelper()

@when_not('logrotate.installed')
def install_logrotate():
    logrotate.modify_configs()
    hookenv.status_set('active', 'Unit is ready.')
    set_flag('logrotate.installed')

@when('config.changed')
def config_changed():
    hookenv.status_set('maintenance', 'Modifying configs.')
    logrotate.modify_configs()
    hookenv.status_set('active', 'Unit is ready.')
