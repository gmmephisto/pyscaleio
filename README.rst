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
