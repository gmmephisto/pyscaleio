from __future__ import unicode_literals

from collections import Mapping

from inflection import camelize, underscore
from object_validator import validate, ValidationError
from object_validator import DictScheme, List, String, Integer, Bool

from psys import Error
from six import text_type

import pyscaleio
from pyscaleio import constants
from pyscaleio import exceptions


class BaseResource(Mapping):
    """Base resource model."""

    __scheme__ = {
        "id": String(),
        "links": List(
            DictScheme({
                "href": String(),
                "rel": String()
            }), optional=True
        )
    }
    __resource__ = None

    @staticmethod
    def _get_client(**kwargs):
        host, client = kwargs.get("host"), kwargs.get("client")
        if host and client:
            raise Error("Invalid configuration")

        if client:
            if not isinstance(client, pyscaleio.ScaleIOClient):
                raise exceptions.ScaleIOInvalidClient()
            return client
        else:
            return pyscaleio.get_client(host)

    @classmethod
    def _get_name(cls):
        resource = cls.__resource__
        if not resource:
            resource = camelize(underscore(cls.__name__))
        return resource

    @classmethod
    def _get_scheme(cls):
        scheme = {}
        for base in cls.mro():
            if bool(
                issubclass(base, BaseResource) and
                getattr(base, "__scheme__", None)
            ):
                scheme.update(base.__scheme__)

        return DictScheme(scheme, ignore_unknown=True)

    @classmethod
    def create(cls, instance, **kwargs):
        """Created instance of resource."""

        client = cls._get_client(**kwargs)
        instance_id = client.create_instance_of(cls._get_name(), instance)

        return cls(instance_id, **kwargs)

    @classmethod
    def one(cls, instance_id, **kwargs):
        """Returns instance of resource."""

        return cls(instance_id, **kwargs)

    @classmethod
    def all(cls, instance_ids=None, **kwargs):
        """Returns list of resource instances."""

        client = cls._get_client(**kwargs)
        if not instance_ids:
            instances = client.get_instances_of(cls._get_name())
        else:
            if isinstance(instance_ids, basestring):
                instance_ids = (instance_ids,)
            instances = client.perform_actions_on(
                cls._get_name(), "queryBySelectedIds", {"ids": instance_ids})

        return [cls(instance=instance, client=client)
            for instance in instances
        ]

    def __init__(self, instance_id=None, instance=None, host=None, client=None):
        self._client = self._get_client(host=host, client=client)
        self._scheme = {}

        if instance_id and instance:
            raise Error("Both 'instance_id' and 'instance' cannot be specified.")

        if instance_id:
            instance = self._client.get_instance_of(self._get_name(), instance_id)

        self._instance = self._validate(instance or {})

    def __getitem__(self, key):
        return self._instance[key]

    def __iter__(self):
        return iter(self._instance)

    def __len__(self):
        return len(self._instance)

    def _validate(self, instance):
        try:
            return validate("instance", instance, self._get_scheme())
        except ValidationError as e:
            raise exceptions.ScaleIOValidationError(e)

    def update(self):
        """Updates resource instance."""

        instance = self._client.get_instance_of(self._get_name(), self["id"])
        instance = self._validate(instance)

        fields = set(list(instance) + list(self._instance))
        for field in fields:
            try:
                instance[field]
            except KeyError:
                del self._instance[field]
            else:
                self._instance[field] = instance[field]

    def perform(self, action, data):
        """Performs action on resource instance."""

        return self._client.perform_action_on(self._get_name(), self["id"], action, data)


class System(BaseResource):
    """System resource model."""

    __scheme__ = {
        "name": String(optional=True),
        "restrictedSdcModeEnabled": Bool(),
    }

    @property
    def name(self):
        return self.get("name")

    @property
    def is_restricted(self):
        return self["restrictedSdcModeEnabled"]


class Volume(BaseResource):
    """Volume resource model."""

    __scheme__ = {
        "name": String(optional=True),
        "mappedSdcInfo": List(DictScheme({
            "sdcId": String(),
            "sdcIp": String(),
            "limitIops": Integer(),
            "limitBwInMbps": Integer()
        }), optional=True),
        "useRmcache": Bool(),
        "sizeInKb": Integer(),
        "storagePoolId": String(),
        "volumeType": String(
            choices=constants.VOLUME_TYPES
        ),
    }

    @classmethod
    def one_by_name(cls, name, **kwargs):
        """Returns volume instance by name."""

        client = cls._get_client(**kwargs)
        volume_id = client.perform_actions_on(
            cls.__name__, "queryIdByKey", {"name": name})

        return cls(volume_id, **kwargs)

    @classmethod
    def create(cls, size, pool, name=None, rmcache=None, thin=True, **kwargs):
        """Creates Volume instance.

        :param size: volume size in GB (required)
        :param pool: storage pool id (required)
        :param name: volume name
        :param thin: is volume 'thin' or 'thick' provisioned
        :param rmcache: volume rmcache

        :returns: volume instance
        """

        volume_size = (size * constants.GIGABYTE) // constants.KILOBYTE
        volume = {
            "volumeSizeInKb": text_type(volume_size),
            "storagePoolId": pool
        }
        if name:
            volume["name"] = name
        if rmcache:
            volume["useRmcache"] = rmcache

        volume["volumeType"] = constants.VOLUME_TYPE_THICK
        if thin:
            volume["volumeType"] = constants.VOLUME_TYPE_THIN

        return super(Volume, cls).create(volume, **kwargs)

    @property
    def name(self):
        return self.get("name")

    @property
    def size(self):
        return self["sizeInKb"] * constants.KILOBYTE

    @property
    def type(self):
        return self.get("volumeType")

    @property
    def exports(self):
        return self.get("mappedSdcInfo", [])

    def rename(self, name):
        """Changes volume name.

        :param name: new volume name
        """

        return super(Volume, self).perform(
            "setVolumeName", {"newName": name})

    def resize(self, size):
        """Changes volumes size.

        :param size: new volume size in GB (required)
        """

        return super(Volume, self).perform(
            "setVolumeSize", {"sizeInGB": size})

    def export(self, sdc_id=None, sdc_guid=None, multiple=False):
        """Exports volume to specified SDC."""

        if sdc_id and sdc_guid:
            raise Error("Use either 'sdc_id' or 'sdc_guid', not both.")

        data = {}
        if sdc_id:
            data["sdcId"] = sdc_id
        if sdc_guid:
            data["guid"] = sdc_guid

        if multiple:
            data["allowMultipleMappings"] = "TRUE"

        return super(Volume, self).perform("addMappedSdc", data)

    def unexport(self, sdc_id=None, sdc_guid=None):
        """Unexports volume from specified SDC."""

        if sdc_id and sdc_guid:
            raise Error("Use either 'sdc_id' or 'sdc_guid', not both.")

        data = {}
        if sdc_id:
            data["sdcId"] = sdc_id
        elif sdc_guid:
            data["guid"] = sdc_guid
        else:
            data["allSdcs"] = ""

        return super(Volume, self).perform("removeMappedSdc", data)

    def delete(self, mode=constants.VOLUME_REMOVE_ONLY_ME):
        """Removes volume with specified mode.

        :param mode: volume remove mode
        """

        return super(Volume, self).perform(
            "removeVolume", {"removeMode": mode})
