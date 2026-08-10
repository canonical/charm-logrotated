"""Tests for install-hook bootstrap setup."""

import os
import runpy
import stat


def test_configure_charm_tmp_uses_private_charm_directory(tmp_path):
    """TMPDIR should stay on the charm filesystem and be owner-only."""
    charm_dir = tmp_path / "charm"
    charm_dir.mkdir()
    environ = {"JUJU_CHARM_DIR": str(charm_dir)}
    hook_namespace = runpy.run_path("hooks/install")
    configure_charm_tmp = hook_namespace["configure_charm_tmp"]

    tmp_dir = configure_charm_tmp(environ)

    assert tmp_dir == str(charm_dir / "tmp")
    assert environ["TMPDIR"] == tmp_dir
    assert os.path.isdir(tmp_dir)
    assert stat.S_IMODE(os.stat(tmp_dir).st_mode) == 0o700
