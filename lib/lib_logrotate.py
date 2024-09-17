"""Logrotate module."""

import json
import os
import re

from charmhelpers.core import hookenv

LOGROTATE_DIR = "/etc/logrotate.d/"


class LogrotateHelper:
    """Helper class for logrotate charm."""

    def __init__(self):
        """Init function."""
        self.retention = hookenv.config("logrotate-retention")
        self.override_size_regex = re.compile(r"size [\d]*(k|M|G)?")
        self.override_interval_regex = re.compile("(daily|weekly|monthly|yearly)")
        self.override = json.loads(hookenv.config("override"))
        self.override_files = self.get_override_files()

    def read_config(self):
        """Read changes from disk.

        Config changed/install hooks dumps config out to disk,
        Here we read that config to update the cronjob
        """
        config_file = open("/etc/logrotate_cronjob_config", "r")
        lines = config_file.read()
        lines = lines.split("\n")

        self.retention = int(lines[2])

    def modify_configs(self):
        """Modify the logrotate config files."""
        for config_file in os.listdir(LOGROTATE_DIR):
            file_path = LOGROTATE_DIR + config_file

            logrotate_file = open(file_path, "r")
            content = logrotate_file.read()
            logrotate_file.close()

            mod_contents = self.modify_content(content, file_path)

            mod_contents = self.modify_header(mod_contents)

            logrotate_file = open(file_path, "w")
            logrotate_file.write(mod_contents)
            logrotate_file.close()

    def get_override_files(self):
        """Return paths for files to be overrided."""
        return [
            override_entry["path"]
            for override_entry in self.override
            if "path" in override_entry  # skip those without "path".
        ]

    def get_override_settings(self, file_path):
        """Return settings in key:value pairs for the file_path requested.

        param: file_path: path to the file for manual settings.
        """
        size = None
        rotate = None
        interval = None
        for override_entry in self.override:
            if file_path == override_entry["path"]:
                size = override_entry.get("size")
                rotate = override_entry.get("rotate")
                interval = override_entry.get("interval")
        return {"rotate": rotate, "interval": interval, "size": size}

    def modify_content(self, content, file_path):
        """Edit the content of a logrotate file."""
        # Split the contents in a logrotate file in separate entries (if
        # multiple are found in the file) and put in a list for further
        # processing
        split = content.split("\n")
        items = []
        string = ""
        for row in split:
            string += row + "\n"
            if "}" in row:
                string = "\n" + string.strip()
                items.append(string)
                string = ""
                continue

        # Work on each item - checking the rotation configuration and setting
        # the rotate option to the appropriate value
        results = []
        rotate_pattern = re.compile(r"rotate \d+\.?[0-9]*")

        override_settings = {}
        if file_path in self.override_files:
            override_settings = self.get_override_settings(file_path)

        count = override_settings.get("rotate")
        for item in items:
            # Override rotate, if defined
            if file_path in self.override_files:
                if count is None:
                    results.append(item)
                    continue
            else:
                count = self.calculate_count(item, self.retention)
            rotate = "rotate {}".format(count)
            # if rotate is missing, add it as last line in the item entry
            if rotate_pattern.findall(item):
                result = rotate_pattern.sub(rotate, item)
            else:
                result = item.replace("}", "    " + rotate + "\n}")

            results.append(result)

        results = "\n".join(results) + "\n"

        # Override interval or size, if defined
        size = override_settings.get("size")
        interval = override_settings.get("interval")
        if size is not None:
            results = self.modify_size_directive(results, size=size)
        elif interval is not None:
            results = self.modify_interval_directive(results, interval=interval)

        return results

    def modify_size_directive(self, results, size=None):
        """Modify size directive."""
        # Replace interval with size if interval is defined
        if self.override_interval_regex.search(results):
            return self.override_interval_regex.sub(f"size {size}", results)
        # Replace old size with new size
        else:
            return self.override_size_regex.sub(f"size {size}", results)

    def modify_interval_directive(self, results, interval=None):
        """Modify interval directive."""
        # Replace old interval with new interval
        if self.override_interval_regex.search(results):
            return self.override_interval_regex.sub(interval, results)
        # Replace size with interval if size is removed
        else:
            return self.override_size_regex.sub(interval, results)

    def modify_header(self, content):
        """Add Juju headers to the file."""
        header = (
            "# Configuration file maintained by Juju. Local changes may be overwritten"
        )
        content = [
            row for row in content.splitlines() if row and not row.startswith(header)
        ]
        return "\n".join([header, *content]) + "\n"

    @staticmethod
    def calculate_count(item, retention):
        """Calculate rotate based on rotation interval. Always round up."""
        # Fallback to default lowest retention - days
        # better to keep the logs than lose them
        count = retention
        # Daily 1:1 to configuration retention period (in days)
        if "daily" in item:
            count = retention
        # Weekly rounding up, as weeks are 7 days
        if "weekly" in item:
            count = int(round(retention / 7))
        # Monthly default 30 days and round up because of 28/31 days months
        if "monthly" in item:
            count = int(round(retention / 30))
        # For every 360 days - add 1 year
        if "yearly" in item:
            count = retention // 360 + 1 if retention > 360 else 1

        return count
