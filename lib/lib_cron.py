import os
import re
from lib_logrotate import LogrotateHelper

class CronHelper:
    """Helper class for logrotate charm."""

    @classmethod
    def __init__(self):
        """Init function"""
        self.cronjob_check_paths = [ "hourly", "daily", "weekly", "monthly" ]
        self.cronjob_logrotate_cron_file = "charm-logrotate"


    @classmethod
    def read_config(self):
        """Config changed/install hooks dumps config out to disk,
        Here we read that config to update the cronjob"""

        config_file = open("/etc/logrotate_cronjob_config", "r")
        lines = config_file.read() 
        lines = lines.split('\n')

        if lines[0] == 'True':
            self.cronjob_enabled = True
        else:
            self.cronjob_enabled = False

        self.cronjob_frequency = int(self.cronjob_check_paths.index(lines[1]))


    @classmethod
    def install_cronjob(self):
        """If logrotate-cronjob config option is set to True 
           install cronjob.  Otherwise cleanup"""

        clean_up_file = self.cronjob_frequency if self.cronjob_enabled else -1

        if self.cronjob_enabled is True:
            path_to_lib = os.path.realpath(__file__)
            cron_file_path = "/etc/cron." + self.cronjob_check_paths[clean_up_file] \
                             + "/" + self.cronjob_logrotate_cron_file

            # upgrade to template if logic increases
            cron_file = open(cron_file_path, 'w')
            cron_file.write("#!/bin/sh\n/usr/bin/python3 " + path_to_lib + "\n\n")
            cron_file.close()
            os.chmod(cron_file_path,700)
            
        self.cleanup_cronjob(clean_up_file)


    @classmethod
    def cleanup_cronjob(self, frequency = -1):
        """Cleanup previous config"""
        for i in range(4):
            if frequency != i:
                path = "/etc/cron." + self.cronjob_check_paths[i] + "/" +\
                       self.cronjob_logrotate_cron_file
                if os.path.exists(path):
                    os.remove(path)

    @classmethod
    def update_logrotate_etc(self):
        """Run logrotate update config"""
        logrotate = LogrotateHelper()
        logrotate.read_config()
        logrotate.modify_configs()


def main():
    cronHelper = CronHelper()
    cronHelper.read_config()
    cronHelper.update_logrotate_etc()
    cronHelper.install_cronjob()


if __name__ == '__main__':
    main()
