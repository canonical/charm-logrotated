"""Cron helper module."""
import os
import re
import subprocess

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
        clean_up_file = self.cronjob_frequency if self.cronjob_enabled else -1

        if self.cronjob_enabled is True:
            cronjob_path = os.path.realpath(__file__)
            cron_file_path = (
                self.cronjob_base_path
                + self.cronjob_check_paths[clean_up_file]
                + "/"
                + self.cronjob_logrotate_cron_file
            )

            logrotate_unit = hookenv.local_unit()
            python_venv_path = os.getcwd().replace("charm", "") + ".venv/bin/python3"
            # upgrade to template if logic increases
            cron_file = open(cron_file_path, "w")
            cron_job = """#!/bin/bash
/usr/bin/sudo /usr/bin/juju-run {} "{} {}"
""".format(
                logrotate_unit, python_venv_path, cronjob_path
            )
            cron_file.write(cron_job)
            cron_file.close()
            os.chmod(cron_file_path, 700)

            # update cron.daily schedule if logrotate-cronjob-frequency set to "daily"
            if (
                self.validate_cron_conf()
                and self.cronjob_frequency == 1
                and self.cron_daily_schedule[0] != "unset"
            ):
                self.update_cron_daily_schedule()

        self.cleanup_cronjob(clean_up_file)

    def cleanup_cronjob(self, frequency=-1):
        """Cleanup previous config."""
        if frequency == -1:
            for check_path in self.cronjob_check_paths:
                path = (
                    self.cronjob_base_path
                    + check_path
                    + "/"
                    + self.cronjob_logrotate_cron_file
                )
                if os.path.exists(path):
                    os.remove(path)
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
        split_schedule = schedule.split(",")
        cron_daily_time = split_schedule[1].split(":")

        if split_schedule[0] == "set":
            cron_daily_hour = cron_daily_time[0]
            cron_daily_minute = cron_daily_time[1]

        if split_schedule[0] == "random":
            cron_daily_end_time = split_schedule[2].split(":")

            cron_daily_hour = cron_daily_time[0] + "~" + cron_daily_end_time[0]
            cron_daily_minute = cron_daily_time[1] + "~" + cron_daily_end_time[1]

        cron_daily_timestamp = cron_daily_minute + " " + cron_daily_hour + "\t"
        cron_pattern = re.compile(r".*\/etc\/cron.daily.*")
        with open(r"/etc/crontab", "r") as crontab:
            data = crontab.read()
        cron_daily = cron_pattern.findall(data)

        updated_cron_daily = ""
        if cron_daily:
            updated_cron_daily = re.sub(
                r"\d?\d(~\d\d)?\s\d?\d(~\d\d)?\t", cron_daily_timestamp, cron_daily[0]
            )
            data = data.replace(cron_daily[0], updated_cron_daily)
            with open(r"/tmp/crontab", "w") as crontab:
                crontab.write(data)

            subprocess.check_output(["sudo", "crontab", "-u", "root", "/tmp/crontab"])

        return updated_cron_daily

    def validate_cron_conf(self):
        """Block the unit and exit the hook if there is invalid configuration."""
        try:
            conf = self.cron_daily_schedule
            conf = conf.split(",")
            if conf[0] not in ("unset", "set", "random") or len(conf) > 3:
                raise ValueError(
                    "Invalid value for update-cron-daily-schedule: {}".format(conf)
                )

            conf_mapping = {
                "set": "_validate_set_schedule",
                "random": "_validate_random_schedule",
            }

            conf_handler = conf_mapping.get(conf[0])
            result = eval("self." + conf_handler)(conf)
            return result

        except ValueError as err:
            raise self.InvalidCronConfig(err)

    def _validate_set_schedule(self, conf):
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
    hookenv.status_set("maintenance", "Executing cron job.")
    cronhelper = CronHelper()
    cronhelper.read_config()
    cronhelper.update_logrotate_etc()
    cronhelper.install_cronjob()
    hookenv.status_set("active", "Unit is ready.")


if __name__ == "__main__":
    main()
