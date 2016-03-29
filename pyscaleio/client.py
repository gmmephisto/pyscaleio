from __future__ import unicode_literals

import json
import psys
import requests

from urlparse import urljoin

requests.packages.urllib3.disable_warnings()
"""Disable certificate warnings."""

__api_version__ = 2.0
"""ScaleIO API Version."""


class ScaleIOError(psys.Error):
    def __init__(self, code, message, error_code=None):
        super(ScaleIOError, self).__init__(
            "ScaleIOError: code={0}, message={1}", code, message
        )
        self.status_code = code
        self.error_code = error_code or 0


class ScaleIOAuthError(ScaleIOError):
    def __init__(self):
        super(ScaleIOAuthError, self).__init__(401, "Unauthorized")


class ScaleIOMalformedError(ScaleIOError):
    def __init__(self):
        super(ScaleIOMalformedError, self).__init__(500, "Malformed response")


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
                raise ScaleIOAuthError()
            else:
                raise

        self.token = json.loads(response.text)
        self.__session.auth = (self.user, self.token)

    def __expired(self):
        """Handle session expiring."""

        self.token = None
        self.__session.auth = None

        self.login()

    def __error(self, exc):
        """Handle request error."""

        error = None
        try:
            error = json.loads(exc.response.text)
        except (ValueError, TypeError):
            raise exc
        else:
            raise ScaleIOError(error["httpStatusCode"],
                               error["message"],
                               error["errorCode"])

    def __response(self, response):
        """Handle response object."""

        try:
            return json.loads(psys.u(response.text))
        except (ValueError, TypeError):
            raise ScaleIOMalformedError()

    def _send_request(self, method, url, data=None, headers=None):
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

    def get(self, path):
        return self._send_request(
            method="get", url=urljoin(self.endpoint, path))

    def post(self, path, data):
        return self._send_request(
            method="post", url=urljoin(self.endpoint, path), data=data)


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

        path = "types/{type}/instances".format(type=resourse)

        if params:
            query = path + "?"
            for param, value in params.items():
                query += "{0}={1}".format(param, value)

        return self._session.get(path)

    def get_instance_of(self, resourse, resourse_id):
        """Returns instance of specified resourse type by id."""

        return self._session.get("instances/{type}::{id}".format(
            type=resourse, id=resourse_id)
        )
