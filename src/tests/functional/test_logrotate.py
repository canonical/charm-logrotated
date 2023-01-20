#!/usr/bin/python3.6
"""Main module for functional testing."""

import os

import pytest

import pytest_asyncio

pytestmark = pytest.mark.asyncio
SERIES = ["bionic", "focal", "jammy"]


############
# FIXTURES #
############


@pytest_asyncio.fixture(scope="module", params=SERIES)
async def deploy_app(request, model):
    """Deploy the logrotate charm as a subordinate of ubuntu."""
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


#########
# TESTS #
#########


async def test_deploy(deploy_app):
    """Tst the deployment."""
    assert deploy_app.status == "active"
