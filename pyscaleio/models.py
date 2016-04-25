from __future__ import unicode_literals

import os
from six import text_type as str
from collections import Mapping, Sequence

from inflection import camelize, underscore
from object_validator import validate, ValidationError
from object_validator import DictScheme, List, String, Integer, Bool

import pyscaleio
from pyscaleio import config
from pyscaleio import constants
from pyscaleio import exceptions
from pyscaleio import utils


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
    """Data scheme for instance validation."""

    __parents__ = None
    """
    References to parent resources by fields.

    Example:
        frozenset([
            ("parentField", "ResourceClassName")
        ])
    """

    __resource__ = None
    """
    Custom resource name that overrides default
    name based on name of resource class.
    """

    @classmethod
    def _get_name(cls):
        """Returns resource name.

        Attention: for internal use only!
        """

        resource = cls.__resource__
        if not resource:
            resource = camelize(underscore(cls.__name__))
        return resource

    @classmethod
    def _get_scheme(cls):
        """Returns resource scheme for proper validation.

        Attention: for internal use only!
        """

        scheme = {}
        for base in cls.mro():
            if bool(
                issubclass(base, BaseResource) and
                getattr(base, "__scheme__", None)
            ):
                scheme.update(base.__scheme__)

        return DictScheme(scheme, ignore_unknown=True)

    @classmethod
    def one(cls, instance_id, **kwargs):
        """Returns instance of resource.

        :param instance_id: id of resource instance

        :returns: instance of resource
        """

        return cls(instance_id, **kwargs)

    @pyscaleio.inject
    @classmethod
    def all(cls, client, instance_ids=None, **kwargs):
        """Returns list of resource instances.

        :param instance_ids: list of instance ids (optional)

        :returns: list of resource instances
        """

        if not instance_ids:
            instances = client.get_instances_of(cls._get_name())
        else:
            if isinstance(instance_ids, basestring):
                instance_ids = (instance_ids,)
            instances = client.perform_action_on_type(
                cls._get_name(), "queryBySelectedIds", {"ids": instance_ids})

        return [cls(instance=instance, client=client)
            for instance in instances
        ]

    @pyscaleio.inject
    def __init__(self, client, instance_id=None, instance=None):
        self._client = client
        self._scheme = {}

        if instance_id and instance:
            raise exceptions.ScaleIONotBothParameters("instance_id", "instance")

        if instance_id:
            instance = self._client.get_instance_of(self._get_name(), instance_id)

        self._instance = self._validate(instance or {})

    def __getitem__(self, key):
        return self._instance[key]

    def __iter__(self):
        return iter(self._instance)

    def __len__(self):
        return len(self._instance)

    @property
    def links(self):
        return self["links"]

    def _validate(self, instance):
        """Validates the instance if resource according to scheme.

        Attention: for internal use only!
        """

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


class EditableResource(BaseResource):
    """Resource model with editable properties."""

    def perform(self, action, data):
        """Performs action on resource instance.

        :param action: action name
        :param data: action data payload
        """

        return self._client.perform_action_on(self._get_name(), self["id"], action, data)


class MutableResource(EditableResource):
    """Resource model that can be created/deleted."""

    @pyscaleio.inject
    @classmethod
    def create(cls, client, instance, **kwargs):
        """Created instance of resource.

        :param instance: instance payload
        """

        instance_id = client.create_instance_of(cls._get_name(), instance)

        return cls(instance_id, **kwargs)

    def delete(self, data=None):
        """Deletes instance of resource.

        :param data: action data payload (optional)
        """

        self.perform("remove{0}".format(self._get_name()), data or {})


class System(EditableResource):
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


class ProtectionDomain(MutableResource):
    """ProtectionDomain resource model."""

    __scheme__ = {
        "name": String(),
        "systemId": String(),
    }
    __parents__ = frozenset([
        ("systemId", "System")
    ])

    @property
    def name(self):
        return self["name"]


class StoragePool(MutableResource):
    """StoragePool resource model."""

    __scheme__ = {
        "name": String(optional=True),
        "protectionDomainId": String(),
        "checksumEnabled": Bool(),
        "useRfcache": Bool(),
    }
    __parents__ = frozenset([
        ("protectionDomainId", "ProtectionDomain")
    ])

    @pyscaleio.inject
    @classmethod
    def one_by_name(cls, client, name, domain_name):
        """Returns StoragePool instance by name and protection domain name.

        :param name: storage pool name
        :param domain_name: protection domain name

        :rtype: pyscaleio.StoragePool
        """

        data = {
            "name": name,
            "protectionDomainName": domain_name
        }
        pool_id = client.perform_action_on_type(
            cls._get_name(), "queryIdByKey", data)

        return cls(pool_id, client=client)

    @pyscaleio.inject
    @classmethod
    def create(cls, client, domain, checksum=False, rfcache=False, name=None, **kwargs):
        """Creates StoragePool instance.

        :param domain: protection domain id (required)
        :param checksum: enable checksum protection (default is False)
        :param rfcache: use read-only flash cache (default is False)

        :rtype: pyscaleio.StoragePool
        """

        pool = {
            "protectionDomainId": domain,
            "checksumEnabled": utils.bool_to_str(checksum),
            "useRfcache": utils.bool_to_str(rfcache),
        }
        if name:
            pool["name"] = name

        return super(StoragePool, cls).create(pool, **kwargs)

    @property
    def name(self):
        return self.get("name")

    @property
    def checksum_enabled(self):
        return self["checksumEnabled"]

    @property
    def rfcache_enabled(self):
        return self["useRfcache"]

    def create_volume(self, size, **kwargs):
        """Creates Volume instance in current StoragePool.

        :param size: volume size in GB (required)

        :rtype: pyscaleio.Volume
        """

        kwargs["client"] = self._client
        return Volume.create(size, self["id"], **kwargs)


class VTree(BaseResource):
    """Volume Tree (VTree) resource model."""

    __scheme__ = {
        "name": String(optional=True),
        "baseVolumeId": String(),
        "storagePoolId": String(),
    }

    __parents__ = frozenset([
        ("baseVolumeId", "Volume"),
        ("storagePoolId", "StoragePool")
    ])


class Sdc(MutableResource):
    """SDC resource model."""

    __scheme__ = {
        "name": String(optional=True),
        "sdcIp": String(),
        "sdcGuid": String(),
        "sdcApproved": Bool(),
    }
    __parents__ = frozenset([
        ("systemId", "System")
    ])

    @pyscaleio.inject
    @classmethod
    def all_approved(cls, client, **kwargs):
        """Returns list of all approved SDCs."""

        instances = client.perform_action_on_type(
            cls._get_name(), "queryAllApprovedSdc", {})

        return [cls(instance=instance, client=client)
            for instance in instances
        ]

    @pyscaleio.inject
    @classmethod
    def one_by_ip(cls, client, ip_address, **kwargs):
        """Returns SDC instance by specified IP address.

        :param ip_address: IP address of SDC

        :rtype: pyscaleio.SDC
        """

        instance_id = client.perform_action_on_type(
            cls._get_name(), "queryIdByKey", {"ip": ip_address})

        return cls(instance_id, client=client)

    @property
    def name(self):
        return self.get("name")

    @property
    def ip(self):
        return self["sdcIp"]

    @property
    def guid(self):
        return self["sdcGuid"]

    @property
    def is_approved(self):
        return self["sdcApproved"]


class ExportsInfo(Sequence):
    """Information about volume exports."""

    __scheme__ = List(DictScheme({
        "sdcId": String(),
        "sdcIp": String(),
        "limitIops": Integer(),
        "limitBwInMbps": Integer()
    }), optional=True)

    def __init__(self, data=None):
        self._data = data or []

    def __getitem__(self, index):
        return self._data[index]

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        if isinstance(key, Sdc):
            return key["id"] in (e["sdcId"] for e in self._data)
        else:
            super(ExportsInfo, self).__contains__(key)


class Volume(MutableResource):
    """Volume resource model."""

    __scheme__ = {
        "name": String(optional=True),
        "mappedSdcInfo": ExportsInfo.__scheme__,
        "useRmcache": Bool(),
        "sizeInKb": Integer(),
        "storagePoolId": String(),
        "volumeType": String(choices=constants.VOLUME_TYPES),
        "ancestorVolumeId": String(optional=True),
    }
    __parents__ = frozenset([
        ("ancestorVolumeId", "Volume"),
        ("storagePoolId", "StoragePool"),
        ("vtreeId", "VTree"),
    ])

    @pyscaleio.inject
    @classmethod
    def one_by_name(cls, client, name, **kwargs):
        """Returns volume instance by name.

        :param name: volume name (required)

        :rtype: pyscaleio.Volume
        """

        volume_id = client.perform_action_on_type(
            cls._get_name(), "queryIdByKey", {"name": name})

        return cls(volume_id, **kwargs)

    @classmethod
    def create(cls, size, pool, name=None, rmcache=None, thin=True, **kwargs):
        """Creates Volume instance.

        :param size: volume size in GB (required)
        :param pool: storage pool id (required)
        :param name: volume name
        :param thin: is volume 'thin' or 'thick' provisioned
        :param rmcache: volume rmcache

        :rtype: pyscaleio.Volume
        """

        volume_size = (size * constants.GIGABYTE) // constants.KILOBYTE
        volume = {
            "volumeSizeInKb": str(volume_size),
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
        return ExportsInfo(self.get("mappedSdcInfo"))

    @property
    def path(self):
        device_name = config.VOLUME_NAME.format(
            system_id=self._client.system["id"],
            volume_id=self["id"]
        )
        return os.path.join(config.VOLUME_PREFIX, device_name)

    def rename(self, name):
        """Changes volume name.

        :param name: new volume name
        """

        return super(Volume, self).perform("setVolumeName", {"newName": name})

    def resize(self, size):
        """Changes volumes size.

        :param size: new volume size in GB (required)
        """

        return super(Volume, self).perform("setVolumeSize", {"sizeInGB": str(size)})

    def snapshot(self, name=None):
        """Creates snapshot of current volume.

        :param name: snapshot name
        """

        snapshot = {"volumeId": self["id"]}
        if name:
            snapshot["snapshotName"] = name

        result = self._client.system.perform(
            "snapshotVolumes", {"snapshotDefs": [snapshot]})

        return Volume(result["volumeIdList"][0])

    def throttle(self, sdc_id=None, sdc_guid=None, iops=None, mbps=None):
        """Throttles I/O on current volume.

        :param iops: I/O operations in seconds (> 10)
        :param mbps: network bandwidth as megabytes in seconds
        """

        if sdc_id and sdc_guid:
            raise exceptions.ScaleIONotBothParameters("sdc_id", "sdc_guid")

        if iops is None and mbps is None:
            raise exceptions.ScaleIORequiredParameters("iops", "mbps")

        if iops is not None and iops != 0 and iops <= 10:
            raise exceptions.ScaleIOInvalidLimit("iops", "must be greater than 10.")

        if mbps is not None:
            mbps = mbps * constants.KILOBYTE
            if bool(mbps % constants.KILOBYTE):
                raise exceptions.ScaleIOInvalidLimit("mbps", "must be granular to 1024 KB")

        data = {}
        if sdc_id:
            data["sdcId"] = sdc_id
        if sdc_guid:
            data["guid"] = sdc_guid
        if iops is not None:
            data["iopsLimit"] = str(iops)
        if mbps is not None:
            data["bandwidthLimitInKbps"] = str(mbps)

        return super(Volume, self).perform("setMappedSdcLimits", data)

    def export(self, sdc_id=None, sdc_guid=None, multiple=False):
        """Exports volume to specified SDC.

        :param sdc_id: id of SDC instance
        :param sdc_guid: guid of SDC instance
        :param multiple: allows export to multiple SDCs (optional)
        """

        if sdc_id and sdc_guid:
            raise exceptions.ScaleIONotBothParameters("sdc_id", "sdc_guid")

        data = {}
        if sdc_id:
            data["sdcId"] = sdc_id
        if sdc_guid:
            data["guid"] = sdc_guid

        if multiple:
            data["allowMultipleMappings"] = utils.bool_to_str(multiple)

        return super(Volume, self).perform("addMappedSdc", data)

    def unexport(self, sdc_id=None, sdc_guid=None):
        """Unexports volume from specified SDC.
        Without parameters unexports volume from all SDCs

        :param sdc_id: id of SDC instance
        :param sdc_guid: guid if SDC instance
        """

        if sdc_id and sdc_guid:
            raise exceptions.ScaleIONotBothParameters("sdc_id", "sdc_guid")

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

        :param mode: volume remove mode (optional)
        """

        return super(Volume, self).delete({"removeMode": mode})
