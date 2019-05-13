from unittest.mock import patch

class TestLogrotateHelper():
    def test_pytest(self):
        assert True


    def test_daily_retention_count(self, logrotate):
        logrotate.retention = 90
        contents = '/var/log/some.log {\n  rotate 123\n  daily\n}'
        count = logrotate.calculate_count(contents)
        assert count == 90

    def test_weekly_retention_count(self, logrotate):
        logrotate.retention = 21
        contents = '/var/log/some.log {\n  rotate 123\n  weekly\n}'
        count = logrotate.calculate_count(contents)
        assert count == 3

    def test_monthly_retention_count(self, logrotate):
        logrotate.retention = 60
        contents = '/var/log/some.log {\n  rotate 123\n  monthly\n}'
        count = logrotate.calculate_count(contents)
        assert count == 2

    def test_yearly_retention_count(self, logrotate):
        logrotate.retention = 180
        contents = '/var/log/some.log {\n  rotate 123\n  yearly\n}'
        count = logrotate.calculate_count(contents)
        assert count == 1

    def test_modify_content(self, logrotate):
        logrotate.retention = 42
        contents = '/var/log/some.log {\n  rotate 123\n  daily\n}\n/var/log/other.log {\n  rotate 456\n  weekly\n}'
        mod_contents = logrotate.modify_content(contents)
        expected_contents = '/var/log/some.log {\n  rotate 42\n  daily\n}\n\n/var/log/other.log {\n  rotate 6\n  weekly\n}\n'
        assert mod_contents == expected_contents
