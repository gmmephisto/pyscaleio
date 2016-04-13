from __future__ import unicode_literals

import json
import psys
import six

import mock
import pytest
import httmock

from object_validator import String, Integer, DictScheme

import pyscaleio
from pyscaleio import constants
from pyscaleio import exceptions

from pyscaleio import ScaleIOClient
from pyscaleio.manager import ScaleIOClientsManager
from pyscaleio.models import BaseResource, Volume, System


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
    ("StoragePool", "StoragePool"), ("SDC", "Sdc"),
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

        with pytest.raises(psys.Error):
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

        with pytest.raises(psys.Error):
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


def test_volume_model(client, modelklass):

    volume_payload = mock_resource_get(Volume._get_name(), "test", {
        "id": "test",
        "sizeInKb": (8 * constants.GIGABYTE) // constants.KILOBYTE,
        "storagePoolId": "test_pool",
        "useRmcache": False,
        "volumeType": constants.VOLUME_TYPE_THICK
    })
    sysem_payload = mock_resources_get(System._get_name(), [{
        "id": "system"
    }])
    with httmock.HTTMock(login_payload, volume_payload, sysem_payload):
        volume = Volume("test")

        assert volume.name is None
        assert volume.size == 8 * constants.GIGABYTE
        assert volume.type == constants.VOLUME_TYPE_THICK
        assert isinstance(volume.exports, list)
        assert not volume.exports

        with mock.patch("pyscaleio.models.System.__scheme__", {}):
            assert volume.path == "emc-vol-system-test"
