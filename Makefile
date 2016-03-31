.PHONY: env changelog clean

VENV    ?= .venv
PIP     ?= $(VENV)/bin/pip
PYTHON  ?= $(VENV)/bin/python
PYVER   ?= python2.7
PACKAGE := pyscaleio

all: env

env:
ifeq ($(wildcard $(PIP)),)
	virtualenv $(VENV) --python=$(PYVER)
endif
	$(PIP) uninstall $(PACKAGE) -q -y ||:
	$(PYTHON) setup.py develop

ifneq ($(wildcard $(PIP)),)
changelog:
	$(PYTHON) setup.py install
endif

clean:
	@rm -rf .coverage .coverage-report .venv/ build/ dist/ \
			.tox/ *.egg* .eggs/ rpms/ srpms/ *.tar.gz *.rpm
