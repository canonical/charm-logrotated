from unittest.mock import patch

class TestLogroateHelper():
    def test_pytest(self):
        assert True


    def test_daily_retention_count(self, logrotate):
        self.retention = 90
        contents = '/var/log/some.log {\n  rotate 123\n  daily\n}'
        count = logrotate.calculate_count(self, contents)
        assert count == 90

    def test_weekly_retention_count(self, logrotate):
        self.retention = 21
        contents = '/var/log/some.log {\n  rotate 123\n  weekly\n}'
        count = logrotate.calculate_count(self, contents)
        assert count == 3

    def test_monthly_retention_count(self, logrotate):
        self.retention = 60
        contents = '/var/log/some.log {\n  rotate 123\n  monthly\n}'
        count = logrotate.calculate_count(self, contents)
        assert count == 2

    def test_yearly_retention_count(self, logrotate):
        self.retention = 180
        contents = '/var/log/some.log {\n  rotate 123\n  yearly\n}'
        count = logrotate.calculate_count(self, contents)
        assert count == 1
