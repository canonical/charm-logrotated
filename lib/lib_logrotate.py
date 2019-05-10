import os
import re

from charmhelpers.core import hookenv


LOGROTATE_DIR = "/etc/logrotate.d/"


class LogrotateHelper:
    """Helper class for logrotate charm."""

<<<<<<< HEAD
    @classmethod
=======
>>>>>>> 713c82f3bdc9044c9dabad820540869abc000164
    def __init__(self):
        """Init function"""

        self.retention = hookenv.config('logrotate-retention')

<<<<<<< HEAD
    @classmethod
=======
>>>>>>> 713c82f3bdc9044c9dabad820540869abc000164
    def modify_configs(self):
        """Modify the logrotate config files."""

        for config_file in os.listdir(LOGROTATE_DIR):
            file_path = LOGROTATE_DIR + config_file

            logrotate_file = open(file_path, 'r')
            content = logrotate_file.read()
            logrotate_file.close()

            mod_contents = self.modify_content(content)

            logrotate_file = open(file_path, 'w')
            logrotate_file.write(mod_contents)
            logrotate_file.close()

            hookenv.log('Changed configuration for {}'.format(file_path))


<<<<<<< HEAD
    @classmethod
=======
>>>>>>> 713c82f3bdc9044c9dabad820540869abc000164
    def modify_content(self, content):
        """Helper function to edit the content of a logrotate file."""

        # Split the content in a logroatate file to separate entries (if
        # multiple are found in the file) and put in a list for further
        # processing
        split = content.split('\n')
        items = []
        string = ""
        for row in split:
            string += row + '\n'
            if '}' in row:
                items.append(string)
                string = ""
                continue

        # Work on each item - checking the rotation configuration and setting
        # the rotate option to the apropriate value
        results = []
        for item in items:
            count = self.calculate_count(item)
            rotate = 'rotate {}'.format(count)
            result = re.sub(r'rotate \d+\.?[0-9]*', rotate, item)
            results.append(result)

        results = '\n'.join(results)

        return results


<<<<<<< HEAD
    @classmethod
=======
>>>>>>> 713c82f3bdc9044c9dabad820540869abc000164
    def calculate_count(self, item):
        """Calculate rotate based on rotation interval. Always round up."""

        # Daily 1:1 to configuration retention period (in days)
        if 'daily' in item:
            count = self.retention
        # Weekly rounding up, as weeks are 7 days
        if 'weekly' in item:
            count = int(round(self.retention/7))
        # Monthly default 30 days and round up because of 28/31 days months
        if 'monthly' in item:
            count = int(round(self.retention/30))
        # For every 360 days - add 1 year
        if 'yearly' in item:
            count = self.retention // 360 + 1 if self.retention > 360 else 1

        return count
