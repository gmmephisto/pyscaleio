.PHONY: env changelog sources srpm rpm clean

DIST    ?= epel-6-x86_64

VENV    ?= .venv
PIP     ?= $(VENV)/bin/pip
PYTHON  ?= $(VENV)/bin/python
PYVER   ?= python2.7
PROGRAM := pyscaleio
PACKAGE := python-scaleio

VERSION := $(shell rpm -q --qf "%{version}\n" --specfile $(PACKAGE).spec | head -1)
RELEASE := $(shell rpm -q --qf "%{release}\n" --specfile $(PACKAGE).spec | head -1)


all: env

env:
ifeq ($(wildcard $(PIP)),)
	virtualenv $(VENV) --python=$(PYVER)
endif
	$(PIP) uninstall $(PROGRAM) -q -y ||:
	$(PYTHON) setup.py develop

ifneq ($(wildcard $(PIP)),)
changelog:
	$(PYTHON) setup.py install
endif

sources: clean
	@git archive --format=tar --prefix="$(PROGRAM)-$(VERSION)/" \
		$(shell git rev-parse --verify HEAD) | gzip > "$(PROGRAM)-$(VERSION).tar.gz"

srpm: sources
	@mkdir -p srpms/
	rpmbuild -bs --define "_sourcedir $(CURDIR)" \
		--define "_srcrpmdir $(CURDIR)/srpms" $(PACKAGE).spec

rpm:
	@mkdir -p rpms/$(DIST)
	/usr/bin/mock -r $(DIST) \
		--rebuild srpms/$(PACKAGE)-$(VERSION)-$(RELEASE).src.rpm \
		--resultdir rpms/$(DIST) --no-cleanup-after

copr: srpm
	@copr-cli build --nowait miushanov/pyscaleio \
		srpms/$(PACKAGE)-$(VERSION)-$(RELEASE).src.rpm

pypi:
	@python setup.py sdist bdist_wheel upload

clean:
	@rm -rf .coverage .coverage-report .venv/ build/ dist/ \
			.tox/ *.egg* .eggs/ rpms/ srpms/ *.tar.gz *.rpm
