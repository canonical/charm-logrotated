"""Main unit test module."""

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


class TestCronHelper:
    """Main cron test class."""

    def test_cron_daily_schedule_unset(self, cron):
        """Test the validation of unset update-cron-daily-schedule config value."""
        cron_config = cron()
        cron_config.cronjob_enabled = True
        cron_config.cronjob_frequency = 1
        cron_config.cron_daily_schedule = "unset"

        assert cron_config.validate_cron_conf()

    @pytest.mark.parametrize(
        ("cron_schedule, exp_pattern"),
        [
            ("random,06:00,07:50", "00~50 06~07"),
            ("random,06:00,07:00", "00~00 06~07"),
            ("random,07:00,07:45", "00~45 07~07"),
            ("set,08:00", "00 08"),
            ("unset", "25 6"),
        ],
    )
    def test_cron_daily_schedule(self, cron, cron_schedule, exp_pattern):
        """Test the validate and update random cron.daily schedule."""
        cron_config = cron()
        cron_config.cronjob_enabled = True
        cron_config.cronjob_frequency = 1
        cron_config.cron_daily_schedule = cron_schedule

        assert cron_config.validate_cron_conf()

        updated_cron_daily = cron_config.update_cron_daily_schedule()

        assert updated_cron_daily.split("\t")[0] == exp_pattern

    @pytest.mark.parametrize(
        ("cron_schedule"),
        [
            ("random,07:00,06:50"),
            ("random,07:50,07:00"),
            ("random,59:50,07:00"),
            ("random,07:00,39:00"),
            ("set,28:00"),
            ("set,02:80"),
        ],
    )
    def test_invalid_cron_daily_schedule(self, cron, cron_schedule):
        """Test the validate and update random cron.daily schedule."""
        cron_config = cron()
        cron_config.cronjob_enabled = True
        cron_config.cronjob_frequency = 1
        cron_config.cron_daily_schedule = cron_schedule

        with pytest.raises(cron_config.InvalidCronConfig) as err:
            cron_config.validate_cron_conf()

        assert err.type == cron_config.InvalidCronConfig
