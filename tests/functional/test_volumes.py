import os
import pytest

import pyscaleio
from pyscaleio import ScaleIOClient, ScaleIOClientsManager
from pyscaleio import System, StoragePool, Volume, SDC
from pyscaleio import exceptions
from pyscaleio import constants


TEST_NAME_PREFIX = "pyscaleiotest_"
"""Prefix for instance name."""


def _is_test_name(instance):
    """Returns True if the instance created by functonal test."""

    return instance.name and instance.name.startswith(TEST_NAME_PREFIX)


def _get_test_name(string):
    """Returns test name for resource."""

    return "pyscaleiotest_{0}".format(string)


@pytest.fixture(scope="module", autouse=True)
def client(request):
    """ScaleIO client fixture."""

    client = ScaleIOClient.from_args(
        os.getenv("scaleio_host"),
        os.getenv("scaleio_user"),
        os.getenv("scaleio_passwd"),
        os.getenv("scaleio_is_secure")
    )
    pyscaleio.add_client(client)
    request.addfinalizer(ScaleIOClientsManager().deregister)
    return client


def cleanup_volumes():
    """Removes all volumes from ScaleIO created by functional tests."""

    for volume in Volume.all():
        if not _is_test_name(volume):
            pass
        while volume.exports:
            volume.unexport()
            volume.update()
        volume.delete()

    assert not [v for v in Volume.all() if _is_test_name(v)]


@pytest.fixture(autouse=True)
def setup_teardown(request):
    """Fixture that performs setup/teardown per test."""

    cleanup_volumes()
    request.addfinalizer(cleanup_volumes)


@pytest.fixture
def storage_pool(request):
    return StoragePool.all()[-1]


@pytest.fixture
def system(request):
    return System.all()[-1]


def test_get_system():

    assert len(System.all()) == 1


def test_create_volume(storage_pool):

    volume = Volume.create(4, storage_pool["id"], name=_get_test_name(1))

    assert volume.name == _get_test_name(1)
    assert volume.size == 8 * constants.GIGABYTE

    volume.delete()
    with pytest.raises(exceptions.ScaleIOError):
        volume.update()

    # TODO: 'NotFound' error should be 404 instead of 500
    # assert e.value.status_code == 404
    # ScaleIOError: code=500, message=Could not find the volume


def test_volume_resize(storage_pool):

    volume = Volume.create(4, storage_pool["id"], name=_get_test_name(1))

    assert volume.size == 8 * constants.GIGABYTE

    with pytest.raises(exceptions.ScaleIOError) as e:
        volume.resize(10)
    assert e.value.status_code == 400

    with pytest.raises(exceptions.ScaleIOError) as e:
        volume.resize(6)
    assert e.value.status_code == 400

    volume.update()
    assert volume.size == 8 * constants.GIGABYTE

    volume.resize(16)
    volume.update()
    assert volume.size == 16 * constants.GIGABYTE


def test_volume_export(storage_pool, system):

    if system.is_restricted:
        if not SDC.all_approved():
            pytest.skip("Now one approved SDC in restricted mode.")

    volume = Volume.create(8, storage_pool["id"], name=_get_test_name(1))
    assert not volume.exports

    if system.is_restricted:
        sdc = SDC.all_approved()[-1]
    else:
        sdc = SDC.all()[-1]

    volume.export(sdc_id=sdc["id"])
    volume.update()

    assert volume.exports
    assert len(volume.exports) == 1
    assert volume.exports[0]["sdcId"] == sdc["id"]
    assert volume.exports[0]["sdcIp"] == sdc.ip

    with pytest.raises(exceptions.ScaleIOError):
        volume.export(sdc_id=sdc["id"])
        volume.export(sdc_guid=sdc["guid"])
