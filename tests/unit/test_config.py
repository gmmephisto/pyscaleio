from __future__ import unicode_literals

import pytest
import mock

import pyscaleio
from pyscaleio import exceptions


def test_config_apply():

    assert pyscaleio.config.NETWORK_TIMEOUT == 30
    assert pyscaleio.config.REQUEST_RETRIES == 3
    assert pyscaleio.config.VOLUME_PREFIX == "/dev/disk/by-id"

    with mock.patch("pyscaleio.config", autospec=True):
        pyscaleio.configure(network_timeout=10)
        assert pyscaleio.config.NETWORK_TIMEOUT == 10

        pyscaleio.configure(volume_prefix="/dev")
        assert pyscaleio.config.VOLUME_PREFIX == "/dev"

        with pytest.raises(exceptions.ScaleIOConfigError):
            pyscaleio.configure(network_timeout="timeout")

        with pytest.raises(exceptions.ScaleIOConfigError):
            pyscaleio.configure(unexist_field="value")
