#!/usr/bin/python3.6

import os
import pytest

pytestmark = pytest.mark.asyncio
SERIES = ['xenial',
          'bionic',
          pytest.param('cosmic', marks=pytest.mark.xfail(reason='canary')),
          ]

############
# FIXTURES #
############

@pytest.fixture(scope='module',
                params=SERIES)
async def deploy_app(request, model):
    '''Deploys the logrotate charm as a subordinate of ubuntu'''
    release = request.param

    await model.deploy(
        'ubuntu',
        application_name='ubuntu-' + release,
        series=release,
        channel='stable'
    )
    logrotate_app = await model.deploy(
        '{}/builds/logrotate'.format(os.getenv('JUJU_REPOSITORY')),
        application_name='logrotate-' + release,
        series=release,
        num_units=0,
    )
    await model.add_relation(
        'ubuntu-' + release,
        'logrotate-' + release
    )

    await model.block_until(lambda: logrotate_app.status == 'active')
    yield logrotate_app


@pytest.fixture(scope='module')
async def unit(deploy_app):
    '''Returns the logrotate unit we've deployed'''
    return deploy_app.units.pop()

#########
# TESTS #
#########


async def test_deploy(deploy_app):
    assert deploy_app.status == 'active'
