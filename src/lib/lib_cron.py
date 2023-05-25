"""Cron helper module."""
import os
import re

from charmhelpers.core import hookenv

from lib_logrotate import LogrotateHelper


class CronHelper:
    """Helper class for logrotate charm."""

    def __init__(self):
        """Init function."""
        self.cronjob_base_path = "/etc/cron."
        self.cronjob_etc_config = "/etc/logrotate_cronjob_config"
        self.cronjob_check_paths = ["hourly", "daily", "weekly", "monthly"]
        self.cronjob_logrotate_cron_file = "charm-logrotate"

    class InvalidCronConfig(ValueError):
        """Raised for invalid cron.daily config input."""

        pass

    def read_config(self):
        """Read the configuration from the file.

        Config changed/install hooks dumps config out to disk,
        Here we read that config to update the cronjob.
        """
        config_file = open(self.cronjob_etc_config, "r")
        lines = config_file.read()
        lines = lines.split("\n")

        if lines[0] == "True":
            self.cronjob_enabled = True
        else:
            self.cronjob_enabled = False

        self.cronjob_frequency = int(self.cronjob_check_paths.index(lines[1]))

        self.cron_daily_schedule = lines[3]

    def install_cronjob(self):
        """Install the cron job task.

        If logrotate-cronjob config option is set to True install cronjob,
        otherwise cleanup.
        """
        self.cleanup_cronjob_files()

        if self.cronjob_enabled is True:
            cronjob_path = os.path.realpath(__file__)
            cron_file_path = (
                self.cronjob_base_path
                + self.cronjob_check_paths[self.cronjob_frequency]
                + "/"
                + self.cronjob_logrotate_cron_file
            )

            logrotate_unit = hookenv.local_unit()
            python_venv_path = os.getcwd().replace("charm", "") + ".venv/bin/python3"
            # upgrade to template if logic increases
            cron_job = """#!/bin/bash
/usr/bin/sudo /usr/bin/juju-run {} "{} {}"
""".format(
                logrotate_unit, python_venv_path, cronjob_path
            )
            with open(cron_file_path, "w") as cron_file:
                cron_file.write(cron_job)
            os.chmod(cron_file_path, 0o755)

            # update cron.daily schedule if logrotate-cronjob-frequency set to "daily"
            if self.cronjob_frequency == 1 and self.validate_cron_conf():
                self.update_cron_daily_schedule()
        else:
            self.cleanup_etc_config()

    def cleanup_cronjob_files(self):
        """Cleanup previous cronjob files."""
        for check_path in self.cronjob_check_paths:
            path = os.path.join(
                self.cronjob_base_path + check_path, self.cronjob_logrotate_cron_file
            )
            if os.path.exists(path):
                os.remove(path)

    def cleanup_etc_config(self):
        """Cleanup the saved config in /etc directory."""
        if os.path.exists(self.cronjob_etc_config):
            os.remove(self.cronjob_etc_config)

    def update_logrotate_etc(self):
        """Run logrotate update config."""
        logrotate = LogrotateHelper()
        logrotate.read_config()
        logrotate.modify_configs()

    def update_cron_daily_schedule(self):
        """Update the cron.daily schedule."""
        schedule = self.cron_daily_schedule
        schedule_type, _, schedule_value = schedule.partition(",")
        cron_daily_time = schedule_value.split(":")

        if schedule_type == "set":
            cron_daily_hour = cron_daily_time[0]
            cron_daily_minute = cron_daily_time[1]

        elif schedule_type == "random":
            cron_daily_start, _, cron_daily_end = schedule_value.partition(",")
            cron_end_hour, _, cron_end_minute = cron_daily_end.partition(":")
            cron_start_hour, _, cron_start_minute = cron_daily_start.partition(":")

            cron_daily_hour = cron_start_hour + "~" + cron_end_hour
            cron_daily_minute = cron_start_minute + "~" + cron_end_minute

        elif schedule_type == "unset":
            # Revert to default ubuntu/debian values for daily cron job
            cron_daily_hour = "6"
            cron_daily_minute = "25"
        else:
            raise RuntimeError("Unknown daily schedule type: {}".format(schedule_type))

        cron_daily_timestamp = cron_daily_minute + " " + cron_daily_hour
        self.write_to_crontab(cron_daily_timestamp)

        return cron_daily_timestamp

    def write_to_crontab(self, cron_daily_timestamp):
        """Write daily cronjob with provided timestamp to /etc/crontab."""
        cron_pattern = re.compile(r".*\/etc\/cron.daily.*")
        with open(r"/etc/crontab", "r") as crontab:
            data = crontab.read()
        cron_daily = cron_pattern.findall(data)

        updated_cron_daily = ""
        if cron_daily:
            updated_cron_daily = re.sub(
                r"\d?\d(~\d\d)?\s\d?\d(~\d\d)?\t",
                cron_daily_timestamp + "\t",
                cron_daily[0],
            )
            updated_data = data.replace(cron_daily[0], updated_cron_daily)
            with open(r"/etc/crontab", "w") as crontab:
                crontab.write(updated_data)

    def validate_cron_conf(self):
        """Block the unit and exit the hook if there is invalid configuration."""
        try:
            conf = self.cron_daily_schedule
            conf = conf.split(",")
            operation = conf[0]
            if operation not in ("unset", "set", "random") or len(conf) > 3:
                raise ValueError(
                    "Invalid value for update-cron-daily-schedule: {}".format(conf)
                )

            result = True
            # run additional validation functions
            if operation == "set":
                result = self._validate_set_schedule(conf)
            elif operation == "random":
                result = self._validate_random_schedule(conf)

            return result

        except ValueError as err:
            hookenv.log(
                "Cron config validation failed: {}".format(err),
                level=hookenv.ERROR,
            )
            hookenv.status_set(
                "blocked", "Cron config validation failed. Check log for more info."
            )
            raise self.InvalidCronConfig(err)

    def _validate_set_schedule(self, conf):
        """Validate update-cron-daily-schedule when the "set" keyword exists."""
        cron_daily_time = conf[1].split(":")
        if not self._valid_timestamp(cron_daily_time):
            raise ValueError(
                "Invalid value for update-cron-daily-schedule: \
                    {}".format(
                    conf[1]
                )
            )
        else:
            return True

    def _validate_random_schedule(self, conf):
        """Validate update-cron-daily-schedule when the "random" keyword exists."""
        cron_daily_start_time = conf[1].split(":")
        cron_daily_end_time = conf[2].split(":")
        if not (
            self._valid_timestamp(cron_daily_start_time)
            and self._valid_timestamp(cron_daily_end_time)
            and int(cron_daily_start_time[0]) <= int(cron_daily_end_time[0])
            and int(cron_daily_start_time[1]) <= int(cron_daily_end_time[1])
        ):
            raise ValueError(
                "Invalid value for update-cron-daily-schedule: \
                    {},{}".format(
                    conf[1], conf[2]
                )
            )
        else:
            return True

    def _valid_timestamp(self, timestamp):
        """Validate the timestamp."""
        return int(timestamp[0]) in range(24) and int(timestamp[1]) in range(60)


def main():
    """Ran by cron."""
    hookenv.log("Executing cron job.", level=hookenv.INFO)
    hookenv.status_set("maintenance", "Executing cron job.")
    cronhelper = CronHelper()
    cronhelper.update_logrotate_etc()
    hookenv.log("Cron job completed.", level=hookenv.INFO)
    hookenv.status_set("active", "Unit is ready.")


if __name__ == "__main__":
    main()
