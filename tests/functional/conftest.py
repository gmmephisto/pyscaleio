from __future__ import unicode_literals

import logging
import os
import pytest

import pyscaleio
from pyscaleio import ScaleIOClient, ScaleIOClientsManager

from . import cleanup_volumes, cleanup_pools


@pytest.fixture(scope="module", autouse=True)
def client(request):
    """ScaleIO client fixture."""

    client = ScaleIOClient.from_args(
        os.getenv("scaleio_host"),
        os.getenv("scaleio_user"),
        os.getenv("scaleio_passwd"),
        int(os.getenv("scaleio_is_secure", 1))
    )
    pyscaleio.add_client(client)
    request.addfinalizer(ScaleIOClientsManager().deregister)
    return client


@pytest.fixture(autouse=True)
def setup_teardown(request):
    """Fixture that performs setup/teardown per test."""

    cleanup_volumes()
    cleanup_pools()
    request.addfinalizer(cleanup_volumes)
    request.addfinalizer(cleanup_pools)


@pytest.fixture(autouse=True, scope="session")
def setup_logging(request):
    """Fixture that setups debug logging."""

    trace_level = os.getenv("scaleio_trace")
    if trace_level:
        logger = logging.getLogger("pyscaleio")
        try:
            logger.setLevel(logging.getLevelName(trace_level.upper()))
        except ValueError:
            logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
            "%Y.%m.%d %H:%M:%S")

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        request.addfinalizer(lambda: logger.removeHandler(handler))
