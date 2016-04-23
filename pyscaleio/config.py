from __future__ import unicode_literals

from six import add_metaclass

from object_validator import validate, ValidationError
from object_validator import Integer, String, DictScheme

import pyscaleio.config
from pyscaleio import exceptions
from pyscaleio import utils


NETWORK_TIMEOUT = 30
"""Timeout for all network operations."""

REQUEST_RETRIES = 3
"""Default retries count for HTTP request."""

VOLUME_PREFIX = "/dev/disk/by-id"
"""Default prefix for volume path."""

VOLUME_NAME = "emc-vol-{system_id}-{volume_id}"
"""
Default name for volume path on SDC.
Must be parametrized with system_id and volume_id.
"""


@add_metaclass(utils.singleton)
class ScaleIOConfig(object):
    """ScaleIO config manager."""

    __scheme__ = {
        "network_timeout": Integer(min=0, optional=True),
        "request_retries": Integer(min=0, optional=True),
        "volume_prefix": String(optional=True),
        "volume_name": String(optional=True),
    }

    @classmethod
    def _get_scheme(cls):
        """Returns config scheme."""

        return DictScheme(cls.__scheme__)

    def _validate(self, options):
        """Validates config."""

        try:
            return validate("config", options, self._get_scheme())
        except ValidationError as e:
            raise exceptions.ScaleIOConfigError(e)

    def apply(self, **options):
        """Applies config options to a config module."""

        self._validate(options)

        for option, value in options.items():
            setattr(pyscaleio.config, option.upper(), value)
