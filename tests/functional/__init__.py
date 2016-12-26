from __future__ import unicode_literals

from six import text_type as str

from pyscaleio import StoragePool, Volume


TEST_NAME_PREFIX = "pyscaleiotest_"
"""Prefix for instance name."""


def _is_test_name(instance):
    """Returns True if the instance created by functonal test."""

    return instance.name and instance.name.startswith(TEST_NAME_PREFIX)


def _get_test_name(string):
    """Returns test name for resource."""

    return TEST_NAME_PREFIX + str(string)


def cleanup_volumes():
    """Removes all volumes from ScaleIO created by functional tests."""

    for volume in Volume.all():
        if not _is_test_name(volume):
            continue
        while volume.exports:
            volume.unexport()
            volume.update()
        volume.delete()

    assert not [v for v in Volume.all() if _is_test_name(v)]


def cleanup_pools():
    """Removes all storage pools from ScaleIO created by functional tests."""

    for pool in StoragePool.all():
        if not _is_test_name(pool):
            continue
        pool.delete()

    assert not [p for p in StoragePool.all() if _is_test_name(p)]
