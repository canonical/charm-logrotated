#!/usr/bin/python3
"""Configurations for tests."""

import mock

import pytest

# If layer options are used, add this to ${fixture}
# and import layer in logrotate
@pytest.fixture
def mock_layers(monkeypatch):
    """Layers mock."""
    import sys
    sys.modules['charms.layer'] = mock.Mock()
    sys.modules['reactive'] = mock.Mock()
    # Mock any functions in layers that need to be mocked here

    def options(layer):
        # mock options for layers here
        if layer == 'example-layer':
            options = {'port': 9999}
            return options
        else:
            return None

    monkeypatch.setattr('lib_logrotate.layer.options', options)


@pytest.fixture
def mock_hookenv_config(monkeypatch):
    """Hookenv mock."""
    import yaml

    def mock_config():
        cfg = {}
        yml = yaml.load(open('./config.yaml'))

        # Load all defaults
        for key, value in yml['options'].items():
            cfg[key] = value['default']

        # Manually add cfg from other layers
        # cfg['my-other-layer'] = 'mock'
        return cfg

    monkeypatch.setattr('lib_logrotate.hookenv.config', mock_config)


@pytest.fixture
def mock_remote_unit(monkeypatch):
    """Remote unit mock."""
    monkeypatch.setattr('lib_logrotate.hookenv.remote_unit', lambda: 'unit-mock/0')


@pytest.fixture
def mock_charm_dir(monkeypatch):
    """Charm dir mock."""
    monkeypatch.setattr('lib_logrotate.hookenv.charm_dir', lambda: '/mock/charm/dir')


@pytest.fixture
def logrotate(tmpdir, mock_hookenv_config, mock_charm_dir, monkeypatch):
    """Logrotate fixture."""
    from lib_logrotate import LogrotateHelper
    helper = LogrotateHelper

    # Any other functions that load helper will get this version
    monkeypatch.setattr('lib_logrotate.LogrotateHelper', lambda: helper)

    return helper
