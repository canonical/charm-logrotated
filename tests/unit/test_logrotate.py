"""Main unit test module."""


class TestLogrotateHelper():
    """Main test class."""

    def test_pytest(self):
        """Simple pytest."""
        assert True

    def test_daily_retention_count(self, logrotate):
        """Test daily retention count."""
        logrotate.retention = 90
        contents = '/var/log/some.log {\n  rotate 123\n  daily\n}'
        count = logrotate.calculate_count(contents, logrotate.retention)
        assert count == 90

    def test_weekly_retention_count(self, logrotate):
        """Test weekly retention count."""
        logrotate.retention = 21
        contents = '/var/log/some.log {\n  rotate 123\n  weekly\n}'
        count = logrotate.calculate_count(contents, logrotate.retention)
        assert count == 3

    def test_monthly_retention_count(self, logrotate):
        """Test monthly retention count."""
        logrotate.retention = 60
        contents = '/var/log/some.log {\n  rotate 123\n  monthly\n}'
        count = logrotate.calculate_count(contents, logrotate.retention)
        assert count == 2

    def test_yearly_retention_count(self, logrotate):
        """Test yearly retention count."""
        logrotate.retention = 180
        contents = '/var/log/some.log {\n  rotate 123\n  yearly\n}'
        count = logrotate.calculate_count(contents, logrotate.retention)
        assert count == 1

    def test_modify_content(self, logrotate):
        """Test the modify_content method."""
        logrotate.retention = 42
        contents = '/log/some.log {\n  rotate 123\n  daily\n}\n/log/other.log {\n  rotate 456\n  weekly\n}'
        mod_contents = logrotate.modify_content(logrotate, contents)
        expected_contents = '/log/some.log {\n  rotate 42\n  daily\n}\n\n/log/other.log {\n  rotate 6\n  weekly\n}\n'
        assert mod_contents == expected_contents
