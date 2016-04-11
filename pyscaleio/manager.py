from __future__ import unicode_literals

from six import add_metaclass

from pyscaleio import exceptions
from pyscaleio.client import ScaleIOClient


class singleton(type):
    """Singleton meta-class."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


@add_metaclass(singleton)
class ScaleIOClientsManager(object):
    """ScaleIO Clients manager."""

    def __init__(self):
        self.__registry_cleanup()

    @property
    def clients(self):
        return self.__clients

    @property
    def default(self):
        return self.__default

    @staticmethod
    def _construct_key(instance):
        """Returns key for ScaleIOClient instance."""

        # TODO: combine key with port if exists
        return instance.session.host

    def __registry_cleanup(self):
        """Cleanups the clients registry."""

        self.__clients = {}
        self.__default = None

    def register(self, instance, default=True):
        """Registers ScaleIOClient instances."""

        if not isinstance(instance, ScaleIOClient):
            raise exceptions.ScaleIOInvalidClient()

        instance_key = self._construct_key(instance)
        if instance_key in self.__clients:
            raise exceptions.ScaleIOClientAlreadyRegistered(instance_key)

        self.__clients[instance_key] = instance
        if not self.__default:
            self.__default = instance

    def get_client(self, instance_key=None):
        """Returns ScaleIOClient instance."""

        if instance_key:
            try:
                return self.__clients[instance_key]
            except KeyError:
                raise exceptions.ScaleIOClientNotRegistered(instance_key)

        if self.__default:
            return self.__default

        raise exceptions.ScaleIOEmptyClientRegistry()

    def deregister(self, instance_key=None):
        """Deregisters ScaleIOClient instances."""

        if instance_key:
            client = self.__clients.pop(instance_key, None)
            if client is self.__default:
                self.__default = None
        else:
            self.__registry_cleanup()
