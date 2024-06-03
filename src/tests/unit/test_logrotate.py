"""Main unit test module."""

import json
import os
from textwrap import dedent
from unittest import mock

from lib_logrotate import LogrotateHelper

import pytest


class TestLogrotateHelper:
    """Main test class."""

    def test_pytest(self):
        """Simple pytest."""
        assert True

    def test_daily_retention_count(self, logrotate):
        """Test daily retention count."""
        logrotate.retention = 90
        contents = "/var/log/apt/history.log {\n  rotate 123\n  daily\n}"
        count = logrotate.calculate_count(contents, logrotate.retention)
        assert count == 90

    def test_weekly_retention_count(self, logrotate):
        """Test weekly retention count."""
        logrotate.retention = 21
        contents = "/var/log/apt/history.log {\n  rotate 123\n  weekly\n}"
        count = logrotate.calculate_count(contents, logrotate.retention)
        assert count == 3

    def test_monthly_retention_count(self, logrotate):
        """Test monthly retention count."""
        logrotate.retention = 60
        contents = "/var/log/apt/history.log {\n  rotate 123\n  monthly\n}"
        count = logrotate.calculate_count(contents, logrotate.retention)
        assert count == 2

    def test_yearly_retention_count(self, logrotate):
        """Test yearly retention count."""
        logrotate.retention = 180
        contents = "/var/log/apt/history.log {\n  rotate 123\n  yearly\n}"
        count = logrotate.calculate_count(contents, logrotate.retention)
        assert count == 1

    def test_modify_content(self, logrotate):
        """Test the modify_content method."""
        file_path = "/var/log/myrandom"
        logrotate.retention = 42
        logrotate.override = []
        logrotate.override_files = []
        contents = (
            "/log/some.log {\n  rotate 123\n  daily\n}\n"
            "/log/other.log {\n  rotate 456\n  weekly\n}"
        )
        mod_contents = logrotate.modify_content(logrotate, contents, file_path)
        expected_contents = (
            "\n/log/some.log {\n  rotate 42\n  daily\n}\n\n"
            "/log/other.log {\n  rotate 6\n  weekly\n}\n"
        )
        assert mod_contents == expected_contents

    def test_empty_line_additions(self, logrotate):
        """Test the modify_content method."""
        file_path = "/etc/logrotate.d/apt"
        logrotate.retention = 42
        logrotate.override = []
        logrotate.override_files = []
        contents = (
            "\n\n\n\n\n/var/log/apt/history.log {\n  rotate 123\n  daily\n}\n\n"
            "\n\n\n/var/log/apt/term.log {\n  rotate 456\n  weekly\n}\n"
        )
        mod_contents = logrotate.modify_content(logrotate, contents, file_path)
        expected_contents = (
            "\n/var/log/apt/history.log {\n  rotate 42\n  daily\n}\n\n"
            "/var/log/apt/term.log {\n  rotate 6\n  weekly\n}\n"
        )
        assert mod_contents == expected_contents

    def test_modify_content_override(self, logrotate):
        """Test the modify_content method."""
        file_path = "/etc/logrotate.d/apt"
        logrotate.retention = 42
        logrotate.override = []
        logrotate.override_files = []
        contents = (
            "/var/log/apt/history.log {\n  rotate 123\n  daily\n}\n"
            "/var/log/apt/term.log {\n  rotate 456\n  weekly\n}"
        )
        mod_contents = logrotate.modify_content(logrotate, contents, file_path)
        expected_contents = (
            "\n/var/log/apt/history.log {\n  rotate 42\n  daily\n}\n\n"
            "/var/log/apt/term.log {\n  rotate 6\n  weekly\n}\n"
        )
        assert mod_contents == expected_contents

    def test_modify_content_with_postrotate_sub(self, logrotate):
        """Test modify_content substitutes if postrotate exists."""
        file_path = "/etc/logrotate.d/apt"
        logrotate.retention = 42
        logrotate.override = []
        logrotate.override_files = []
        contents = (
            "/var/log/apt/history.log {\n"
            "  postrotate\n"
            "    /bin/script\n"
            "  endscript\n"
            "  rotate 123\n"
            "  daily\n}\n"
        )
        mod_contents = logrotate.modify_content(logrotate, contents, file_path)
        expected_contents = (
            "\n/var/log/apt/history.log {\n"
            "  postrotate\n"
            "    /bin/script\n"
            "  endscript\n"
            "  rotate 42\n"
            "  daily\n}\n"
        )
        assert mod_contents == expected_contents

    def test_modify_content_with_postrotate_append(self, logrotate):
        """Test the modify_content appends if postrotate exists."""
        file_path = "/etc/logrotate.d/apt"
        logrotate.retention = 42
        logrotate.override = []
        logrotate.override_files = []
        # fmt: off
        contents = (
            "/var/log/apt/history.log {\n"
            "  postrotate\n"
            "    /bin/script\n"
            "  endscript\n}\n"
        )
        # fmt: on
        mod_contents = logrotate.modify_content(logrotate, contents, file_path)
        expected_contents = (
            "\n/var/log/apt/history.log {\n"
            "  postrotate\n"
            "    /bin/script\n"
            "  endscript\n"
            "    rotate 42\n}\n"
        )
        assert mod_contents == expected_contents

    @pytest.mark.parametrize("header_count", [0, 1, 2, 10])
    def test_modify_header(self, logrotate, header_count):
        """Test the modify_header method works and is idempotent."""
        header = "# Configuration file maintained by Juju. Local changes may be overwritten\n"  # noqa
        content_body = (
            "\n/log/some.log {\n  rotate 42\n  daily\n}\n\n"
            "/log/other.log {\n  rotate 6\n  weekly\n}\n"
        )
        content = (header * header_count) + content_body
        expected_content = (
            header + "/log/some.log {\n  rotate 42\n  daily\n}\n"
            "/log/other.log {\n  rotate 6\n  weekly\n}\n"
        )
        modified_content = logrotate.modify_header(logrotate, content)
        assert modified_content == expected_content

    @pytest.mark.parametrize(
        "test_override,input_contents,expected_contents",
        [
            (
                "[ {} ]",
                "/var/log/apt/history.log {\n  rotate 12\n  daily\n}"
                + "\n/var/log/apt/term.log {\n  rotate 12\n  daily\n}",
                "\n/var/log/apt/history.log {\n  rotate 12\n  daily\n}\n"
                + "\n/var/log/apt/term.log {\n  rotate 12\n  daily\n}\n",
            ),
            (
                '[ {"path": "/etc/logrotate.d/apt", "rotate": 5} ]',
                "/var/log/apt/history.log {\n  rotate 12\n  daily\n}"
                + "\n/var/log/apt/term.log {\n  rotate 12\n  daily\n}",
                "\n/var/log/apt/history.log {\n  rotate 5\n  daily\n}\n"
                + "\n/var/log/apt/term.log {\n  rotate 5\n  daily\n}\n",
            ),
            (
                '[ {"path": "/etc/logrotate.d/apt", "interval": "monthly"} ]',
                "/var/log/apt/history.log {\n  rotate 12\n  daily\n}"
                + "\n/var/log/apt/term.log {\n  rotate 12\n  daily\n}",
                "\n/var/log/apt/history.log {\n  rotate 12\n  monthly\n}\n"
                + "\n/var/log/apt/term.log {\n  rotate 12\n  monthly\n}\n",
            ),
            (
                '[{"path":"/etc/logrotate.d/apt","rotate":5, "interval":"monthly"}]',
                "/var/log/apt/history.log {\n  rotate 12\n  daily\n}"
                + "\n/var/log/apt/term.log {\n  rotate 12\n  daily\n}",
                "\n/var/log/apt/history.log {\n  rotate 5\n  monthly\n}\n"
                + "\n/var/log/apt/term.log {\n  rotate 5\n  monthly\n}\n",
            ),
            (
                '[{"path":"/etc/logrotate.d/apt","rotate":5, "size":"100"}]',
                "/var/log/apt/history.log {\n  rotate 12\n  daily\n}"
                + "\n/var/log/apt/term.log {\n  rotate 12\n  daily\n}",
                "\n/var/log/apt/history.log {\n  rotate 5\n  size 100\n}\n"
                + "\n/var/log/apt/term.log {\n  rotate 5\n  size 100\n}\n",
            ),
            (
                '[{"path":"/etc/logrotate.d/apt","rotate":5, "interval":"monthly",'
                + '"size":"1G"}]',
                "/var/log/apt/history.log {\n  rotate 12\n  daily\n}"
                + "\n/var/log/apt/term.log {\n  rotate 12\n  daily\n}",
                "\n/var/log/apt/history.log {\n  rotate 5\n  size 1G\n}\n"
                + "\n/var/log/apt/term.log {\n  rotate 5\n  size 1G\n}\n",
            ),
        ],
    )
    def test_override_config_option(
        self, test_override, input_contents, expected_contents
    ):
        """Test override config option."""
        with mock.patch("lib_logrotate.hookenv.config") as mock_config:
            mock_config.return_value = "[]"
            file_path = "/etc/logrotate.d/apt"
            logrotate_helper = LogrotateHelper()
            logrotate_helper.retention = 12
            logrotate_helper.override = json.loads(test_override)
            logrotate_helper.override_files = logrotate_helper.get_override_files()
            mod_contents = logrotate_helper.modify_content(input_contents, file_path)
            assert mod_contents == expected_contents

    @pytest.mark.parametrize(
        ("status", "frequency", "retention", "cron_schedule"),
        [
            (True, "hourly", 12, "random,03:00,15:00"),
            (True, "daily", 50, "set,14:00,20:50"),
            (True, "weekly", 120, "random,10:00,18:50"),
            (False, "monthly", 365, "random,06:00,07:00"),
        ],
    )
    def test_read_config(
        self, logrotate, status, frequency, retention, cron_schedule, mocker
    ):
        """Test read_config method."""
        logrotate_crontab_config_content = dedent(
            f"""\
            {status}
            {frequency}
            {retention}
            {cron_schedule}
            """
        )
        mocker.patch(
            "lib_logrotate.open",
            mock.mock_open(read_data=logrotate_crontab_config_content),
        )
        mocker.patch("lib_logrotate.os.path.isfile", return_value=True)

        logrotate.read_config(logrotate)

        assert logrotate.retention == retention


class TestCronHelper:
    """Main cron test class."""

    def test_cron_daily_schedule_unset(self, cron):
        """Test the validation of unset update-cron-daily-schedule config value."""
        cron_config = cron()
        cron_config.cronjob_enabled = True
        cron_config.cronjob_frequency = 1
        cron_config.cron_daily_schedule = "unset"

        assert cron_config.validate_cron_daily_schedule_conf()

    @pytest.mark.parametrize(
        ("cron_schedule, random_hour, random_minute, exp_pattern"),
        [
            ("random,06:00,07:50", "6", "30", "30 6"),
            ("random,07:00,09:00", "9", "5", "5 9"),
            ("random,07:10,10:45", "10", "10", "10 10"),
            ("set,08:00", "0", "0", "00 08"),
            ("unset", "0", "0", "25 6"),
        ],
    )
    def test_update_cron_daily_schedule(
        self, cron, cron_schedule, random_hour, random_minute, exp_pattern, mocker
    ):
        """Test the validate and update random cron.daily schedule."""
        cron_config = cron()
        cron_config.cronjob_enabled = True
        cron_config.cronjob_frequency = 1
        cron_config.cron_daily_schedule = cron_schedule

        mock_write_to_crontab = mocker.Mock()
        mocker.patch.object(cron, "write_to_crontab", new=mock_write_to_crontab)

        mock_get_random_time = mocker.Mock()
        mocker.patch.object(cron, "get_random_time", new=mock_get_random_time)
        mock_get_random_time.return_value = random_hour, random_minute

        updated_cron_daily = cron_config.update_cron_daily_schedule()

        assert cron_config.validate_cron_daily_schedule_conf()
        assert updated_cron_daily.split("\t")[0] == exp_pattern
        mock_write_to_crontab.assert_called_once_with(exp_pattern)

    @pytest.mark.parametrize(
        ("cron_schedule, random_hour, random_minute, exp_pattern"),
        [
            ("invalid", "0", "0", "10 10"),
            ("unknown", "0", "0", "10 10"),
        ],
    )
    def test_invalid_update_cron_daily_schedule(
        self, cron, cron_schedule, random_hour, random_minute, exp_pattern, mocker
    ):
        """Test invalid update cron.daily schedule."""
        cron_config = cron()
        cron_config.cronjob_enabled = True
        cron_config.cronjob_frequency = 1
        cron_config.cron_daily_schedule = cron_schedule

        mock_write_to_crontab = mocker.Mock()
        mocker.patch.object(cron, "write_to_crontab", new=mock_write_to_crontab)

        mock_get_random_time = mocker.Mock()
        mocker.patch.object(cron, "get_random_time", new=mock_get_random_time)
        mock_get_random_time.return_value = random_hour, random_minute

        with pytest.raises(RuntimeError):
            cron_config.update_cron_daily_schedule()

    @pytest.mark.parametrize(
        ("start_time", "end_time"),
        [
            ("06:30", "09:45"),
            ("7:42", "12:35"),
            ("18:10", "21:45"),
            ("2:8", "4:6"),
            ("7:30", "7:30"),
            ("30:25", "32:40"),
        ],
    )
    def test_get_random_time(self, cron, start_time, end_time):
        """Test random time setting for update-cron-daily-schedule."""
        cron_config = cron()

        # generate set containing all possible minutes within time_range
        start_hour, start_minute = [int(t) for t in start_time.split(":")]
        end_hour, end_minute = [int(t) for t in end_time.split(":")]
        all_minutes_in_range = set()
        current_hour = start_hour
        current_minute = start_minute
        while current_hour < end_hour or (
            current_hour == end_hour and current_minute <= end_minute
        ):
            all_minutes_in_range.add(f"{current_hour}:{current_minute}")
            current_minute += 1
            if current_minute == 60:
                current_minute = 0
                current_hour += 1

        # run `get_random_time` multiple times, collect output and
        # see if we're able to obtain all possible minutes in range.
        random_time_set = set()
        for _ in range(5000):
            random_hour, random_minute = cron_config.get_random_time(
                start_time, end_time
            )
            random_time = f"{random_hour}:{random_minute}"
            random_time_set.add(random_time)

        assert all_minutes_in_range == random_time_set

    @pytest.mark.parametrize(
        ("start_time", "end_time"),
        [
            ("09:30", "06:45"),  # start_time > end_time
            ("130:45", "18:125"),  # invalid time
        ],
    )
    def test_invalid_get_random_time(self, cron, start_time, end_time):
        """Test invalid time range arguments for get_random_time."""
        cron_config = cron()
        with pytest.raises(ValueError):
            cron_config.get_random_time(start_time, end_time)

    @pytest.mark.parametrize(
        "cron_daily_timestamp", ["00 08", "25 6", "40 18", "5 7", "20 4", "5 35"]
    )
    def test_write_to_crontab(self, cron, cron_daily_timestamp, mocker):
        """Test function that writes updated data to /etc/crontab."""
        cron_config = cron()
        mock_open = mocker.patch("lib_cron.open")
        mock_handle = mock_open.return_value.__enter__.return_value
        default_crontab_contents = dedent(
            """
            # some comment
            17 *\t* * * root cd / && run-parts --report /etc/cron.hourly
            25 6\t* * root test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.daily )
            47 6\t* * 7 root test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.weekly )
            52 6\t1 * * root test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.monthly )
            #
            """  # noqa
        )
        updated_crontab_contents = dedent(
            f"""
            # some comment
            17 *\t* * * root cd / && run-parts --report /etc/cron.hourly
            {cron_daily_timestamp}\t* * root test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.daily )
            47 6\t* * 7 root test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.weekly )
            52 6\t1 * * root test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.monthly )
            #
            """  # noqa
        )
        mock_handle.read.return_value = default_crontab_contents
        cron_config.write_to_crontab(cron_daily_timestamp)

        mock_open.assert_any_call("/etc/crontab", "r")
        mock_open.assert_any_call("/etc/crontab", "w")
        mock_handle.write.assert_called_with(updated_crontab_contents)

    @pytest.mark.parametrize(
        ("cron_schedule"),
        [
            ("random,06:00,07:00"),
            ("random,7:50,9:30"),
            ("random,15:00,19:30"),
            ("random,08:40,09:20"),
            ("set,8:00"),
            ("set,12:10"),
            ("unset"),
        ],
    )
    def test_valid_cron_daily_schedule(self, cron, cron_schedule):
        """Test valid configuration for cron.daily schedule."""
        cron_config = cron()
        cron_config.cronjob_enabled = True
        cron_config.cronjob_frequency = 1
        cron_config.cron_daily_schedule = cron_schedule
        try:
            cron_config.validate_cron_daily_schedule_conf()
        except cron_config.InvalidCronConfig:
            pytest.fail("InvalidCronConfig should not be raised.")

    @pytest.mark.parametrize(
        ("cron_schedule"),
        [
            ("random,07:00,06:50"),
            ("random,07:50,07:00"),
            ("random,59:50,07:00"),
            ("random,07:00,39:00"),
            ("random,09:20,08:40"),
            ("random,08:00,08:00"),
            ("set,28:00"),
            ("set,02:80"),
            ("invalid_setting"),
        ],
    )
    def test_invalid_cron_daily_schedule(self, cron, cron_schedule):
        """Test invalid configuration for cron.daily schedule."""
        cron_config = cron()
        cron_config.cronjob_enabled = True
        cron_config.cronjob_frequency = 1
        cron_config.cron_daily_schedule = cron_schedule

        with pytest.raises(cron_config.InvalidCronConfig) as err:
            cron_config.validate_cron_daily_schedule_conf()

        assert err.type == cron_config.InvalidCronConfig

    def test_install_cronjob(self, cron, mock_local_unit, mocker):
        """Test install cronjob method."""
        mock_charm_dir = "/mock/unit-logrotated-0/charm"
        mock_exists = mocker.patch("lib_cron.os.path.exists", return_value=True)
        mock_remove = mocker.patch("lib_cron.os.remove")
        mock_chmod = mocker.patch("lib_cron.os.chmod")
        mocker.patch(
            "lib_cron.os.path.realpath",
            return_value=os.path.join(mock_charm_dir, "lib/lib_cron.py"),
        )
        # has_juju_version is used to test for juju3,
        # so keep it false here to verify the original juju2 behaviour.
        mocker.patch(
            "lib_cron.hookenv.has_juju_version",
            return_value=False,
        )
        mocker.patch("lib_cron.os.getcwd", return_value=mock_charm_dir)
        mock_open = mocker.patch("lib_cron.open")
        mock_handle = mock_open.return_value.__enter__.return_value
        mock_write_to_crontab = mocker.Mock()
        mocker.patch.object(cron, "write_to_crontab", new=mock_write_to_crontab)
        expected_files_to_be_removed = [
            "/etc/cron.hourly/charm-logrotate",
            "/etc/cron.daily/charm-logrotate",
            "/etc/cron.weekly/charm-logrotate",
            "/etc/cron.monthly/charm-logrotate",
        ]

        cron_config = cron()
        cron_config.cronjob_enabled = True
        cron_config.cronjob_frequency = 2
        cron_config.cron_daily_schedule = "unset"
        cron_config.install_cronjob()

        mock_exists.assert_has_calls(
            [mock.call(file) for file in expected_files_to_be_removed], any_order=True
        )
        mock_remove.assert_has_calls(
            [mock.call(file) for file in expected_files_to_be_removed], any_order=True
        )
        mock_open.assert_called_once_with("/etc/cron.weekly/charm-logrotate", "w")
        mock_handle.write.assert_called_once_with(
            dedent(
                """\
                #!/bin/bash
                /usr/bin/sudo /usr/bin/juju-run unit-logrotated/0 "/mock/unit-logrotated-0/.venv/bin/python3 /mock/unit-logrotated-0/charm/lib/lib_cron.py"
                """  # noqa
            )
        )
        mock_chmod.assert_called_once_with("/etc/cron.weekly/charm-logrotate", 0o755)

    def test_install_cronjob_juju3(self, cron, mock_local_unit, mocker):
        """Test install cronjob method under juju3."""
        mock_charm_dir = "/mock/unit-logrotated-0/charm"
        mock_exists = mocker.patch("lib_cron.os.path.exists", return_value=True)
        mock_remove = mocker.patch("lib_cron.os.remove")
        mock_chmod = mocker.patch("lib_cron.os.chmod")
        mocker.patch(
            "lib_cron.os.path.realpath",
            return_value=os.path.join(mock_charm_dir, "lib/lib_cron.py"),
        )
        # has_juju_version is used to test for juju3.
        # Set it True here so it thinks it's running under juju3.
        mocker.patch(
            "lib_cron.hookenv.has_juju_version",
            return_value=True,
        )
        mocker.patch("lib_cron.os.getcwd", return_value=mock_charm_dir)
        mock_open = mocker.patch("lib_cron.open")
        mock_handle = mock_open.return_value.__enter__.return_value
        mock_write_to_crontab = mocker.Mock()
        mocker.patch.object(cron, "write_to_crontab", new=mock_write_to_crontab)
        expected_files_to_be_removed = [
            "/etc/cron.hourly/charm-logrotate",
            "/etc/cron.daily/charm-logrotate",
            "/etc/cron.weekly/charm-logrotate",
            "/etc/cron.monthly/charm-logrotate",
        ]

        cron_config = cron()
        cron_config.cronjob_enabled = True
        cron_config.cronjob_frequency = 2
        cron_config.cron_daily_schedule = "unset"
        cron_config.install_cronjob()

        mock_exists.assert_has_calls(
            [mock.call(file) for file in expected_files_to_be_removed], any_order=True
        )
        mock_remove.assert_has_calls(
            [mock.call(file) for file in expected_files_to_be_removed], any_order=True
        )
        mock_open.assert_called_once_with("/etc/cron.weekly/charm-logrotate", "w")
        # should be juju-exec under juju3
        mock_handle.write.assert_called_once_with(
            dedent(
                """\
                #!/bin/bash
                /usr/bin/sudo /usr/bin/juju-exec unit-logrotated/0 "/mock/unit-logrotated-0/.venv/bin/python3 /mock/unit-logrotated-0/charm/lib/lib_cron.py"
                """  # noqa
            )
        )
        mock_chmod.assert_called_once_with("/etc/cron.weekly/charm-logrotate", 0o755)
    def test_install_cronjob_removes_etc_config_when_cronjob_disabled(
        self, cron, mocker
    ):
        """Test that all cronjob related files created upon cronjobs being disabled."""
        mock_exists = mocker.patch("lib_cron.os.path.exists", return_value=True)
        mock_remove = mocker.patch("lib_cron.os.remove")

        expected_files_to_be_removed = [
            "/etc/cron.hourly/charm-logrotate",
            "/etc/cron.daily/charm-logrotate",
            "/etc/cron.weekly/charm-logrotate",
            "/etc/cron.monthly/charm-logrotate",
            "/etc/logrotate_cronjob_config",
        ]
        cron_config = cron()
        cron_config.cronjob_enabled = False
        cron_config.install_cronjob()

        mock_exists.assert_has_calls(
            [mock.call(file) for file in expected_files_to_be_removed], any_order=True
        )
        mock_remove.assert_has_calls(
            [mock.call(file) for file in expected_files_to_be_removed], any_order=True
        )

    @pytest.mark.parametrize(
        ("status", "frequency", "retention", "cron_schedule"),
        [
            (True, "hourly", "12", "random,03:00,15:00"),
            (True, "daily", "50", "set,14:00,20:50"),
            (True, "weekly", "120", "random,10:00,18:50"),
            (False, "monthly", "365", "random,06:00,07:00"),
        ],
    )
    def test_cron_read_config(
        self, cron, status, frequency, retention, cron_schedule, mocker
    ):
        """Test cronjob read_config method."""
        logrotate_crontab_config_content = dedent(
            f"""\
            {status}
            {frequency}
            {retention}
            {cron_schedule}
            """
        )
        mocker.patch(
            "lib_cron.open", mock.mock_open(read_data=logrotate_crontab_config_content)
        )
        mocker.patch("lib_cron.os.path.isfile", return_value=True)

        cron_config = cron()
        cron_config.cronjob_check_paths = ["hourly", "daily", "weekly", "monthly"]
        cron_config.read_config()

        assert cron_config.cronjob_enabled == status
        assert cron_config.cronjob_frequency == int(
            cron_config.cronjob_check_paths.index(frequency)
        )
        assert cron_config.cron_daily_schedule == cron_schedule
