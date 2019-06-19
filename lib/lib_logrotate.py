"""Logrotate module."""
import os
import re

from charmhelpers.core import hookenv

LOGROTATE_DIR = "/etc/logrotate.d/"


class LogrotateHelper:
    """Helper class for logrotate charm."""

    def __init__(self):
        """Init function."""
        self.retention = hookenv.config('logrotate-retention')

    def read_config(self):
        """Read changes from disk.

        Config changed/install hooks dumps config out to disk,
        Here we read that config to update the cronjob
        """
        config_file = open("/etc/logrotate_cronjob_config", "r")
        lines = config_file.read()
        lines = lines.split('\n')

        self.retention = int(lines[2])

    def modify_configs(self):
        """Modify the logrotate config files."""
        for config_file in os.listdir(LOGROTATE_DIR):
            file_path = LOGROTATE_DIR + config_file

            logrotate_file = open(file_path, 'r')
            content = logrotate_file.read()
            logrotate_file.close()

            mod_contents = self.modify_content(content)

            mod_contents = self.modify_header(mod_contents)

            logrotate_file = open(file_path, 'w')
            logrotate_file.write(mod_contents)
            logrotate_file.close()

    def modify_content(self, content):
        """Edit the content of a logrotate file."""
        # Split the contents in a logrotate file in separate entries (if
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
        # the rotate option to the appropriate value
        results = []
        for item in items:
            count = self.calculate_count(item, self.retention)
            rotate = 'rotate {}'.format(count)
            result = re.sub(r'rotate \d+\.?[0-9]*', rotate, item)
            results.append(result)

        results = '\n'.join(results)

        return results

    def modify_header(self, content):
        """Add Juju headers to the file."""
        header = "# Configuration file maintained by Juju. Local changes may be overwritten"

        split = content.split('\n')
        if split[0].startswith(header):
            result = content
        else:
            result = header + '\n' + content

        return result

    @classmethod
    def calculate_count(cls, item, retention):
        """Calculate rotate based on rotation interval. Always round up."""
        # Fallback to default lowest retention - days
        # better to keep the logs than lose them
        count = retention
        # Daily 1:1 to configuration retention period (in days)
        if 'daily' in item:
            count = retention
        # Weekly rounding up, as weeks are 7 days
        if 'weekly' in item:
            count = int(round(retention/7))
        # Monthly default 30 days and round up because of 28/31 days months
        if 'monthly' in item:
            count = int(round(retention/30))
        # For every 360 days - add 1 year
        if 'yearly' in item:
            count = retention // 360 + 1 if retention > 360 else 1

        return count
