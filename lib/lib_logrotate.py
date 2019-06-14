import os
import re


LOGROTATE_DIR = "/etc/logrotate.d/"


class LogrotateHelper:
    """Helper class for logrotate charm."""

    @classmethod
    def __init__(self):
        """Init function"""
        pass

    @classmethod
    def read_config(self):
        """Config changed/install hooks dumps config out to disk,
        Here we read that config to update the cronjob"""

        config_file = open("/etc/logrotate_cronjob_config", "r")
        lines = config_file.read()
        lines = lines.split('\n')

        self.retention = int(lines[2])


    @classmethod
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


    @classmethod
    def modify_content(self, content):
        """Helper function to edit the content of a logrotate file."""

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
            count = self.calculate_count(item)
            rotate = 'rotate {}'.format(count)
            result = re.sub(r'rotate \d+\.?[0-9]*', rotate, item)
            results.append(result)

        results = '\n'.join(results)

        return results

    @classmethod
    def modify_header(self, content):
        """Helper function to add Juju headers to the file."""

	header = "# Configuration file maintained by Juju. Local changes may be overwritten"

        split = content.split('\n')
        if split[0].startswith(header):
            result = content
        else:
            result = header + '\n' + content

        return result

    @classmethod
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
