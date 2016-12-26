from __future__ import unicode_literals

import pytest

from pyscaleio import ProtectionDomain, StoragePool, Volume
from pyscaleio import exceptions

from . import _get_test_name


@pytest.fixture
def domain(request):
    return ProtectionDomain.all()[-1]


@pytest.fixture
def storage_pool(request):
    return StoragePool.all()[-1]


def test_create_storage_pool(domain):

    pool = StoragePool.create(domain["id"], name=_get_test_name(5))

    assert isinstance(pool, StoragePool)
    assert pool.name == _get_test_name(5)
    assert pool["protectionDomainId"] == domain["id"]

    assert pool.checksum_enabled is False
    assert pool.rfcache_enabled is False

    pool.delete()
    with pytest.raises(exceptions.ScaleIOError):
        pool.update()


def test_create_volume_in_storage_pool(domain, storage_pool):

    volume = storage_pool.create_volume(8, name=_get_test_name(1))
    assert isinstance(volume, Volume)
    assert volume.name == _get_test_name(1)

    assert volume["storagePoolId"] == storage_pool["id"]

    with pytest.raises(exceptions.ScaleIOError) as e:
        storage_pool.delete()
    assert "Storage Pool has volumes" in str(e.value)
