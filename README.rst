pyscaleio
=========

.. image:: https://travis-ci.org/gmmephisto/pyscaleio.svg?branch=master
   :target: https://travis-ci.org/gmmephisto/pyscaleio

.. image:: https://coveralls.io/repos/github/gmmephisto/pyscaleio/badge.svg?branch=master
   :target: https://coveralls.io/github/gmmephisto/pyscaleio?branch=master

Python library that provides convenient way to interact with ScaleIO REST API.

- Supported ScaleIO versions: 2.0
- Supported Python versions: 2.6, 2.7, 3.4, 3.5

**Library is under development!**


Features
--------

**Currently supported:**

- Simple API client with base methods according to ScaleIO documentation
- ORM-like models (StoragePool, Volume, etc.)
- Scheme validation for API responses

**TODO:**

- HATEOAS links processing


Installation
------------

Install via **pip**:

.. code-block:: console

   $ pip install pyscaleio


Install as RPM package using **yum** or **dnf** on Fedora/RHEL/CentOS:

.. code-block:: console

   $ dnf copr enable miushanov/pyscaleio
   $ dnf install python-scaleio


Usage
-----

* Create and register API client:

.. code-block:: python

   import pyscaleio

   # create API client
   client = pyscaleio.ScaleIOClient.from_args("gateway_address", "admin", "password")

   # register it for using in models
   pyscaleio.add_client(client)

* Find and modify resources:

.. code-block:: python

   # get all volumes in cluster
   volumes = pyscaleio.Volume.all()
   assert len(volumes) == 1

   # or, get volume by specified id
   volume = pyscaleio.Volume.one_by_name("test_volume")

   # and access some volume attributes
   assert volume.name == "test_volume"
   assert volume.size == 8 * constants.GIGABYTE

   # or, resize it to new size
   volume.resize(16)

   volume.update()  # updates model data
   assert volume.size == 16 * constants.GIGABYTE

* Create or delete resources:

.. code-block:: python

   # create new volume in storage pool
   volume = pyscaleio.Volume.create(16, "storage_pool_id", "new_volume")
   assert volume.name == "new_volume"
   assert volume.size == 16 * constants.GIGABYTE

   # delete volume
   volume = pyscaleio.Volume.one_by_name("test_volume")
   volume.delete()

* Tune client and models options:

.. code-block:: python

   pyscaleio.configure(
      # retries count for each request
      request_retries=0,
      # network timeout for requests
      network_timeout=30,
      # name of exported volume (according to udev/rules.d)
      volume_name="emc-2{system_id}{volume_id}",
      # prefix of exported volume
      volume_prefix="/dev/disk/by-id")

   volume = pyscaleio.Volume.one_by_name("test_volume")
   assert volume.path == "/dev/disk/by-id/emc-27947a0127a79ce60ca29f20900000008"


Tests
-----

Tests for this library divided to unit tests and functional tests.
Functional tests requires ScaleIO installation and available REST API Gateway service. For running functional tests use **tox** environment with name *functional* with passed variables:


* ``scaleio_host`` - IP address or hostname of ScaleIO REST API Gateway
* ``scaleio_user`` - username
* ``scaleio_passwd`` - password
* ``scaleio_is_secure`` - ``1`` for using **https** scheme otherwise ``0`` (optional)
* ``scaleio_trace`` - level of logging to stderr (optional)

Example:

.. code-block:: console

   $ scaleio_host=localhost scaleio_user=admin scaleio_passwd=passwd tox -e functional
