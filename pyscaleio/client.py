from __future__ import unicode_literals

import json
import psys
import requests

from six import add_metaclass
from six.moves.urllib.parse import urljoin

from pyscaleio import exceptions


requests.packages.urllib3.disable_warnings()
"""Disable certificate warnings."""

__api_version__ = 2.0
"""ScaleIO API Version."""


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


class ScaleIOSession(object):
    """ScaleIO session base class."""

    __session = None
    """Session instance."""

    __endpoint = "https://{host}/api/"
    """Endpoint template."""

    def __init__(self, host, user, passwd):
        self.host = host

        self.user = user
        self.passwd = passwd

        # TODO: parametrize timeout
        self.timeout = 30
        # TODO: parametrize retries
        self.retries = 3

        self.token = None
        self.headers = {
            "content-type": "application/json",
            "Accept": "application/json; version={version}".format(
                version=__api_version__
            )
        }
        self.__session = requests.Session()
        self.__session.headers.update(self.headers)

    @property
    def endpoint(self):
        return self.__endpoint.format(host=self.host)

    def __expired(self):
        """Handle session expiring."""

        self.token = None
        self.__session.auth = None

        self.login()

    def __error(self, exc):
        """Handle request error."""

        error = self.__response(exc.response)
        raise exceptions.ScaleIOError(error["httpStatusCode"],
                                      error["message"],
                                      error["errorCode"])

    def __response(self, response):
        """Handle response object."""

        try:
            return json.loads(psys.u(response.text))
        except (ValueError, TypeError):
            raise exceptions.ScaleIOMalformedError()

    def login(self):
        """Logins to ScaleIO REST Gateway."""

        if not self.__session:
            self.__session = requests.Session()

        url = urljoin(self.endpoint, "login")
        auth = (self.user, self.passwd)

        response = self.__session.get(
            url=url, auth=auth,
            allow_redirects=False, verify=False)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                raise exceptions.ScaleIOAuthError()
            else:
                raise

        self.token = self.__response(response)
        self.__session.auth = (self.user, self.token)

    def logout(self):
        """Logouts from ScaleIO REST Gateway and invalidates token."""

        if self.__session and self.token:
            self.__session.get(
                url=urljoin(self.endpoint, "logout"))

        self.token = None
        self.__session.auth = None

    def _send_request(self, method, url, params=None, data=None, headers=None):
        """Base method for sending requests."""

        headers = headers or {}
        retries = self.retries

        if not self.token:
            self.login()

        response = None
        while retries > 0:
            response = self.__session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                timeout=self.timeout,
                allow_redirects=False,
                headers=headers,
                verify=False,
            )
            try:
                response.raise_for_status()
            except requests.HTTPError as e:
                if e.response.status_code == 401:
                    self.__expired()
                    retries -= 1
                    continue
                else:
                    self.__error(e)
            else:
                if not response:
                    retries -= 1
                    continue
                else:
                    return self.__response(response)

    def get(self, path, params=None):
        return self._send_request(method="get",
            url=urljoin(self.endpoint, path), params=params)

    def post(self, path, data):
        return self._send_request(method="post",
            url=urljoin(self.endpoint, path), data=data)


class ScaleIOClient(object):
    """API Client for ScaleIO."""

    _session = None
    """ScaleIO session instance."""

    @classmethod
    def from_args(cls, *args, **kwargs):
        """Initialize from ScaleIOSession args."""

        return cls(session=ScaleIOSession(*args, **kwargs))

    def __init__(self, session):
        if not isinstance(session, ScaleIOSession):
            raise psys.Error(
                "ScaleIOClient must be initalized with ScaleIOSession.")
        self._session = session

    @property
    def session(self):
        return self._session

    def get_version(self):
        """Returns ScaleIO REST API version."""

        return self._session.get("version")

    def get_all_instances(self):
        """Returns all exists instances of all types."""

        return self._session.get("instances")

    def get_instances_of(self, resourse, params=None):
        """Returns list of instances of specified resource."""

        return self._session.get("types/{type}/instances".format(
            type=resourse), params=params
        )

    def get_instance_of(self, resourse, resourse_id):
        """Returns instance of specified resourse type by id."""

        return self._session.get("instances/{type}::{id}".format(
            type=resourse, id=resourse_id)
        )

    def create_instance_of(self, resource, resource_data):
        """Creates instance of specified resource."""

        return self._session.post("types/{type}/instances".format(
            type=resource), data=psys.u(json.dumps(resource_data))
        )

    def perform_action_on(self, resource, resource_id, action, action_data):
        """Performs action on single instnace of specified resource type."""

        return self._session.post("instances/{type}::{id}/action/{action}".format(
            type=resource, id=resource_id, action=action),
            data=psys.u(json.dumps(action_data))
        )

    def perform_actions_on(self, resource, action, action_data):
        """Performs action on all instances of specified resource type."""

        return self._session.post("types/{type}/instances/action/{action}".format(
            type=resource, action=action), data=psys.u(json.dumps(action_data))
        )
