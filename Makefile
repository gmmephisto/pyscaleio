.PHONY: env changelog sources clean

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
	$(PIP) install -U -r ./requirements.txt
	$(PYTHON) setup.py install

ifneq ($(wildcard $(PIP)),)
changelog:
	$(shell $(PIP) freeze | grep pyscaleio) && $(PYTHON) setup.py install
endif

sources: clean
	@git archive --format=tar --prefix="$(PACKAGE)-$(VERSION)/" \
		$(shell git rev-parse --verify HEAD) | gzip > "$(PACKAGE)-$(VERSION).tar.gz"

clean:
	@rm -rf .venv/ build/ dist/ *.egg* .eggs/ rpms/ srpms/ *.tar.gz *.rpm
