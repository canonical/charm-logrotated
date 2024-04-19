#!/usr/bin/python3.6
"""Main module for functional testing."""

import json
import logging
import os
import time

import pytest

import pytest_asyncio

import tenacity

pytestmark = pytest.mark.asyncio
SERIES = ["focal", "jammy"]
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()

############
# FIXTURES #
############


@pytest_asyncio.fixture(scope="module", params=SERIES)
async def deploy_app(request, model):
    """Deploy the logrotate charm as a subordinate of ubuntu."""
    logger.info(f"Starting deployment for: {request.param}")
    release = request.param

    await model.deploy(
        "ubuntu", application_name="ubuntu-" + release, series=release, channel="stable"
    )
    logrotate_app = await model.deploy(
        "{}/logrotated.charm".format(os.getenv("CHARM_LOCATION")),
        application_name="logrotate-" + release,
        series=release,
        num_units=0,
    )
    await model.add_relation("ubuntu-" + release, "logrotate-" + release)

    await model.block_until(lambda: logrotate_app.status == "active")
    yield logrotate_app


@pytest_asyncio.fixture(scope="module")
async def unit(deploy_app):
    """Return the logrotate unit we've deployed."""
    return deploy_app.units.pop()


def parse_logrotate_config(content):
    """Parse logrotate config content into a canonical form."""
    config = []
    configs = []
    for row in content.strip().split("\n"):
        row = row.rstrip()
        if not row:
            continue
        elif "{" in row:
            config = [row]
        elif "}" in row:
            config.append(row)
            configs.append("\n".join(config))
        else:
            config.append(row)
    return configs


async def change_override_option(app, model, path, **directives):
    """Apply changes to override option."""
    test_size = directives.get("size")
    test_rotate = directives.get("rotate")
    test_interval = directives.get("interval")
    test_override_option = {"path": path}
    if test_size:
        test_override_option["size"] = test_size
    if test_rotate:
        test_override_option["rotate"] = test_rotate
    if test_interval:
        test_override_option["interval"] = test_interval
    test_override_option_string = json.dumps([test_override_option])

    await app.set_config({"override": test_override_option_string})
    await model.block_until(lambda: app.status == "active")
    time.sleep(5)  # blocking is not enough, gives some time for the config to change


#########
# TESTS #
#########


async def test_deploy(deploy_app):
    """Tst the deployment."""
    logging.info("Testing deployment status...")
    assert deploy_app.status == "active"


async def test_configure_cron_daily(deploy_app):
    """Test configuring cron.daily schedule for the deployment."""
    logging.info("Testing config cron daily")
    await deploy_app.set_config({"logrotate-cronjob-frequency": "daily"})
    await deploy_app.set_config({"update-cron-daily-schedule": "set,07:00"})
    config = await deploy_app.get_config()

    assert config["logrotate-cronjob-frequency"]["value"] == "daily"
    assert config["update-cron-daily-schedule"]["value"] == "set,07:00"

    assert deploy_app.status == "active"

    await deploy_app.set_config({"logrotate-cronjob-frequency": "daily"})
    await deploy_app.set_config({"update-cron-daily-schedule": "random,06:00,08:20"})
    config = await deploy_app.get_config()

    assert config["logrotate-cronjob-frequency"]["value"] == "daily"
    assert config["update-cron-daily-schedule"]["value"] == "random,06:00,08:20"

    assert deploy_app.status == "active"


async def test_reconfigure_cronjob_frequency(model, deploy_app, unit, jujutools):
    """Test reconfiguration of cronjob frequency."""
    await deploy_app.set_config({"logrotate-cronjob-frequency": "weekly"})
    await model.block_until(lambda: deploy_app.status == "active")
    config = await deploy_app.get_config()

    # Retry because test fails sometimes when cron file isn't ready yet
    for attempt in tenacity.Retrying(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    ):
        with attempt:
            result = await jujutools.run_command(
                "test -f /etc/cron.weekly/charm-logrotate", unit
            )
            weekly_cronjob_exists = result["return-code"] == 0
            assert weekly_cronjob_exists

    result = await jujutools.run_command(
        "test -f /etc/cron.daily/charm-logrotate", unit
    )
    daily_cronjob_exists = result["return-code"] == 0

    assert config["logrotate-cronjob-frequency"]["value"] == "weekly"
    assert not daily_cronjob_exists


async def test_configure_override_01(model, deploy_app, jujutools, unit):
    """Test configuring override for the deployment (interval)."""
    test_path = "/etc/logrotate.d/apt"
    test_rotate = 100
    test_interval = "monthly"
    await change_override_option(
        deploy_app, model, test_path, rotate=test_rotate, interval=test_interval
    )
    logrotate_config_content = await jujutools.file_contents(test_path, unit)
    logrotate_config_content = parse_logrotate_config(logrotate_config_content)
    for config in logrotate_config_content:
        assert test_interval in config
        assert f"rotate {test_rotate}" in config


async def test_configure_override_02(model, deploy_app, jujutools, unit):
    """Test configuring override for the deployment (interval and size)."""
    # test path | rotate | interval | size, size should take precedence over interval
    test_path = "/etc/logrotate.d/apt"
    test_size = "100M"
    test_rotate = 5
    test_interval = "monthly"
    await change_override_option(
        deploy_app,
        model,
        test_path,
        rotate=test_rotate,
        interval=test_interval,
        size=test_size,
    )
    logrotate_config_content = await jujutools.file_contents(test_path, unit)
    logrotate_config_content = parse_logrotate_config(logrotate_config_content)
    for config in logrotate_config_content:
        assert test_interval not in config
        assert f"size {test_size}" in config
        assert f"rotate {test_rotate}" in config


async def test_configure_override_03(model, deploy_app, jujutools, unit):
    """Test configuring override for the deployment (interval -> size)."""
    # Changing from size to interval, and the size should be removed when it's
    # not in override.

    # test path | rotate | size
    test_path = "/etc/logrotate.d/apt"
    test_size = "100k"
    test_rotate = 10
    await change_override_option(
        deploy_app, model, test_path, rotate=test_rotate, size=test_size
    )

    # test path | rotate | interval
    test_size = "100k"
    test_rotate = 20
    test_interval = "daily"
    await change_override_option(
        deploy_app, model, test_path, rotate=test_rotate, interval=test_interval
    )

    logrotate_config_content = await jujutools.file_contents(test_path, unit)
    logrotate_config_content = parse_logrotate_config(logrotate_config_content)
    for config in logrotate_config_content:
        assert test_interval in config
        assert f"size {test_size}" not in config
        assert f"rotate {test_rotate}" in config
