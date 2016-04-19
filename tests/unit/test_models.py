from __future__ import unicode_literals

import json
import psys
import six

import mock
import pytest
import httmock

from object_validator import String, Integer, DictScheme
from six import text_type as str

import pyscaleio
from pyscaleio import constants
from pyscaleio import exceptions

from pyscaleio import ScaleIOClient
from pyscaleio.manager import ScaleIOClientsManager
from pyscaleio.models import BaseResource, Volume, StoragePool, System


@pytest.fixture
def client(request):

    client = ScaleIOClient.from_args("localhost", "admin", "passwd")
    pyscaleio.add_client(client)
    request.addfinalizer(ScaleIOClientsManager().deregister)
    return client


@pytest.fixture
def modelklass(request):

    def generate_klass(name, subclasses, dict):
        if six.PY2:
            name = psys.b(name)
        else:
            name = psys.u(name)
        return type(name, subclasses, dict)
    return generate_klass


@httmock.urlmatch(path=r".*login")
def login_payload(url, request):
    return httmock.response(200,
        json.dumps("some_random_token_string"),
        request=request
    )


def mock_resource_get(resource, resource_id, payload):
    path = r".*/api/instances/{0}::{1}".format(resource, resource_id)

    @httmock.urlmatch(path=path, method="get")
    def instance_of_payload(url, request):
        return httmock.response(200, payload, request=request)
    return instance_of_payload


def mock_resources_get(resource, payload):
    path = r".*/api/types/{0}/instances".format(resource)

    @httmock.urlmatch(path=path, method="get")
    def instances_of_payload(url, request):
        return httmock.response(200, payload, request=request)
    return instances_of_payload


def test_base_model_name(client):

    assert BaseResource.__resource__ is None
    with mock.patch("pyscaleio.models.BaseResource.__scheme__", {}):
        assert BaseResource._get_name() == "BaseResource"
        assert BaseResource(instance={})._get_name() == "BaseResource"

        with mock.patch(
            "pyscaleio.models.BaseResource.__resource__",
            "TestResourceName"
        ):
            assert BaseResource._get_name() == "TestResourceName"
            assert BaseResource(instance={})._get_name() == "TestResourceName"


@pytest.mark.parametrize(("name", "result"), [
    ("Volume", "Volume"), ("VTree", "VTree"),
    ("StoragePool", "StoragePool"), ("Sdc", "Sdc"),
])
def test_custom_model_name(client, modelklass, name, result):

    assert BaseResource.__resource__ is None
    with mock.patch("pyscaleio.models.BaseResource.__scheme__", {}):
        klass = modelklass(name, (BaseResource,), {"__scheme__": {}})
        assert klass._get_name() == result
        assert klass(instance={})._get_name() == result


@pytest.mark.parametrize("scheme", [
    {}, {"id": String()}
])
def test_base_model_scheme(client, modelklass, scheme):

    with mock.patch("pyscaleio.models.BaseResource.__scheme__", scheme):
        result = BaseResource._get_scheme()
        assert isinstance(result, DictScheme)
        assert result._DictScheme__scheme == scheme

        result = BaseResource(instance={"id": "test"})._get_scheme()
        assert isinstance(result, DictScheme)
        assert result._DictScheme__scheme == scheme


@pytest.mark.parametrize(("scheme", "data"), [
    ({"name": String()}, {"name": "test"}),
    (
        {"name": String(), "size": Integer()},
        {"name": "test", "size": 8 * constants.GIGABYTE}
    )
])
def test_custom_model_scheme(client, modelklass, scheme, data):

    base_scheme = {"id": String()}
    full_scheme = base_scheme
    full_scheme.update(scheme)

    data = data
    data.update({"id": "test_id"})

    with mock.patch(
        "pyscaleio.models.BaseResource.__scheme__",
        base_scheme
    ):
        klass = modelklass("Volume", (BaseResource,), {"__scheme__": scheme})
        result = klass._get_scheme()
        assert isinstance(result, DictScheme)
        assert result._DictScheme__scheme == full_scheme

        result = klass(instance=data)._get_scheme()
        assert isinstance(result, DictScheme)
        assert result._DictScheme__scheme == full_scheme


def test_model_get_client(client, modelklass):

    with mock.patch("pyscaleio.models.BaseResource.__scheme__", {}):
        klass = modelklass("Test", (BaseResource,), {"__scheme__": {}})

        assert klass._get_client() == pyscaleio.get_client()
        assert klass(instance={})._get_client() == pyscaleio.get_client()

        second_client = ScaleIOClient.from_args("test_host", "admin", "passwd")
        assert klass._get_client(client=second_client) == second_client
        assert klass(instance={})._get_client(client=second_client) == second_client

        assert klass._get_client(host="localhost") == pyscaleio.get_client()


def test_model_get_client_negative(client, modelklass):

    with mock.patch("pyscaleio.models.BaseResource.__scheme__", {}):
        klass = modelklass("Test", (BaseResource,), {"__scheme__": {}})

        with pytest.raises(exceptions.ScaleIONotBothParameters):
            klass._get_client(client="test", host="test")

        with pytest.raises(exceptions.ScaleIOInvalidClient):
            klass._get_client(client="test")


def test_model_initialize(client, modelklass):

    with mock.patch("pyscaleio.models.BaseResource.__scheme__", {}):
        klass = modelklass("Volume", (BaseResource,), {"__scheme__": {}})

        volume_id = "test"
        volume_payload = mock_resource_get(
            "Volume", volume_id, {"id": volume_id})
        with httmock.HTTMock(login_payload, volume_payload):
            assert klass() == {}
            assert len(klass()) == 0

            assert klass(instance_id=volume_id) == {"id": volume_id}

        assert klass(instance={"id": volume_id}) == {"id": volume_id}


def test_model_initialize_negative(client, modelklass):

    with mock.patch("pyscaleio.models.BaseResource.__scheme__", {}):
        klass = modelklass("Volume", (BaseResource,), {"__scheme__": {}})

        with pytest.raises(exceptions.ScaleIONotBothParameters):
            klass(instance_id="test", instance={"id": "test"})


def test_model_validation(client, modelklass):

    klass = modelklass("Volume", (BaseResource,), {
        "__scheme__": {
            "name": String()
        }
    })

    volume_payload = mock_resource_get("Volume", "test", {
        "id": "test",
        "name": "test_volume"
    })
    with httmock.HTTMock(login_payload, volume_payload):
        volume = klass("test")
        assert volume.get("id") == "test"
        assert volume.get("name") == "test_volume"


def test_model_validation_negative(client, modelklass):

    klass = modelklass("Volume", (BaseResource,), {
        "__scheme__": {
            "name": String()
        }
    })
    volume_payload = mock_resource_get("Volume", "test", {"id": "test"})
    with httmock.HTTMock(login_payload, volume_payload):
        with pytest.raises(exceptions.ScaleIOValidationError) as e:
            klass("test")
        assert "instance['name'] is missing" in str(e)


@pytest.mark.parametrize(("old_payload", "new_payload"), [
    (
        {"id": "test", "name": "test_volume"},
        {"id": "test", "name": "test_volume_changed"},
    ),
    (
        {"id": "test"},
        {"id": "test", "name": "test_volume"},
    ),
    (
        {"id": "test", "name": "test_volume"},
        {"id": "test"},
    )
])
def test_model_update(client, modelklass, old_payload, new_payload):

    klass = modelklass("Volume", (BaseResource,), {
        "__scheme__": {
            "name": String(optional=True)
        }
    })
    volume_payload = mock_resource_get("Volume", "test", old_payload)
    volume_update_payload = mock_resource_get("Volume", "test", new_payload)

    with httmock.HTTMock(login_payload, volume_payload):
        volume = klass("test")
        assert volume == old_payload

    with httmock.HTTMock(volume_update_payload):
        volume.update()
        assert volume == new_payload


def test_volume_model(client):

    volume_payload = mock_resource_get(Volume._get_name(), "test", {
        "id": "test",
        "sizeInKb": (8 * constants.GIGABYTE) // constants.KILOBYTE,
        "storagePoolId": "test_pool",
        "useRmcache": False,
        "volumeType": constants.VOLUME_TYPE_THICK
    })
    system_payload = mock_resources_get(System._get_name(), [{
        "id": "system"
    }])
    with httmock.HTTMock(login_payload, volume_payload, system_payload):
        volume = Volume("test")

        assert volume.name is None
        assert volume.size == 8 * constants.GIGABYTE
        assert volume.type == constants.VOLUME_TYPE_THICK
        assert isinstance(volume.exports, list)
        assert not volume.exports

        with mock.patch("pyscaleio.models.System.__scheme__", {}):
            assert volume.path == "emc-vol-system-test"


@pytest.mark.parametrize(("kw", "result"), [
    ({"sdc_id": "test"}, {"sdcId": "test"}),
    ({"sdc_guid": "test"}, {"guid": "test"}),
    (
        {"sdc_id": "test", "multiple": True},
        {"sdcId": "test", "allowMultipleMappings": "TRUE"}
    ),
])
def test_volume_export(client, kw, result):

    with mock.patch("pyscaleio.models.Volume.__scheme__", {}):
        volume = Volume(instance={"id": "test", "links": []})

    with mock.patch("pyscaleio.ScaleIOClient.perform_action_on") as m:
        volume.export(**kw)
        m.assert_called_once_with("Volume", "test", "addMappedSdc", result)


@pytest.mark.parametrize(("kw", "result"), [
    ({"sdc_id": "test"}, {"sdcId": "test"}),
    ({"sdc_guid": "test"}, {"guid": "test"}),
    ({}, {"allSdcs": ""})
])
def test_volume_unexport(client, kw, result):

    with mock.patch("pyscaleio.models.Volume.__scheme__", {}):
        volume = Volume(instance={"id": "test", "links": []})

    with mock.patch("pyscaleio.ScaleIOClient.perform_action_on") as m:
        volume.unexport(**kw)
        m.assert_called_once_with("Volume", "test", "removeMappedSdc", result)


@pytest.mark.parametrize("method", ["export", "unexport"])
def test_volume_unexport_negative(client, method):

    with mock.patch("pyscaleio.models.Volume.__scheme__", {}):
        volume = Volume(instance={"id": "test", "links": []})

    with mock.patch("pyscaleio.ScaleIOClient.perform_action_on") as m:
        with pytest.raises(exceptions.ScaleIONotBothParameters):
            getattr(volume, method)(**{"sdc_id": "test", "sdc_guid": "test"})
        m.assert_not_called()


@pytest.mark.parametrize(("kw", "result"), [
    ({"name": "test"}, {"name": "test"}),
    ({"rmcache": True}, {"useRmcache": True}),
    ({"thin": False}, {"volumeType": constants.VOLUME_TYPE_THICK}),
])
def test_volume_create(client, kw, result):

    args = (1, "test_pool")
    full_result = {
        "volumeSizeInKb": str(1048576),
        "storagePoolId": "test_pool",
        "volumeType": constants.VOLUME_TYPE_THIN,
    }
    full_result.update(result)

    with mock.patch("pyscaleio.models.MutableResource.create") as m:
        Volume.create(*args, **kw)
        m.assert_called_once_with(full_result)


def test_volume_one_by_name(client):

    volume_id = "test_id"
    volume_name = "test_name"

    volume_payload = mock_resource_get(Volume._get_name(), volume_id, {
        "id": volume_id,
        "name": volume_name
    })

    call_args = (Volume._get_name(), "queryIdByKey", {"name": volume_name})
    with mock.patch("pyscaleio.models.Volume.__scheme__", {}):
        with mock.patch(
            "pyscaleio.ScaleIOClient.perform_actions_on",
            side_effect=[volume_id]
        ) as m:
            with httmock.HTTMock(login_payload, volume_payload):
                volume = Volume.one_by_name(volume_name)
            m.assert_called_once_with(*call_args)

            assert isinstance(volume, Volume)
            assert volume.name == volume_name
            assert volume["id"] == volume_id


@pytest.mark.parametrize(("kw", "result"), [
    ({"checksum": True}, {"checksumEnabled": "TRUE"}),
    ({"rfcache": True}, {"useRfcache": "TRUE"}),
    (
        {"checksum": True, "rfcache": True},
        {"checksumEnabled": "TRUE", "useRfcache": "TRUE"}
    ),
    ({"name": "test_pool"}, {"name": "test_pool"})
])
def test_storage_pool_create(client, kw, result):

    args = ("domain_id",)
    full_result = {
        "protectionDomainId": "domain_id",
        "checksumEnabled": "FALSE",
        "useRfcache": "FALSE",
    }
    full_result.update(result)

    with mock.patch("pyscaleio.models.MutableResource.create") as m:
        StoragePool.create(*args, **kw)
        m.assert_called_once_with(full_result)


def test_storage_pool_one_by_name(client):

    pool_id = "test_id"
    pool_name = "test_name"
    domain_id = "domain_id"
    domain_name = "domain_name"

    pool_payload = mock_resource_get(StoragePool._get_name(), pool_id, {
        "id": pool_id,
        "name": pool_name,
        "protectionDomainId": domain_id,
        "checksumEnabled": False,
        "useRfcache": False,
    })

    call_args = (StoragePool._get_name(), "queryIdByKey", {
        "name": pool_name,
        "protectionDomainName": domain_name,
    })
    with mock.patch(
        "pyscaleio.ScaleIOClient.perform_actions_on",
        side_effect=[pool_id]
    ) as m:
        with httmock.HTTMock(login_payload, pool_payload):
            pool = StoragePool.one_by_name(pool_name, domain_name)
        m.assert_called_once_with(*call_args)

        assert isinstance(pool, StoragePool)
        assert pool.name == pool_name
        assert pool["id"] == pool_id
        assert pool.checksum_enabled is False
        assert pool.rfcache_enabled is False
