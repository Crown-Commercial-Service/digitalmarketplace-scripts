SHELL := /bin/bash
VIRTUALENV_ROOT := $(shell [ -z $$VIRTUAL_ENV ] && echo $$(pwd)/venv || echo $$VIRTUAL_ENV)

.PHONY: virtualenv
virtualenv:
	[ -z $$VIRTUAL_ENV ] && [ ! -d venv ] && python3 -m venv venv || true

.PHONY: requirements
requirements: virtualenv requirements.txt
	${VIRTUALENV_ROOT}/bin/pip install -r requirements.txt

.PHONY: requirements-dev
requirements-dev: virtualenv requirements.txt requirements-dev.txt
	${VIRTUALENV_ROOT}/bin/pip install -r requirements.txt -r requirements-dev.txt

.PHONY: freeze-requirements
freeze-requirements: virtualenv requirements-dev requirements.in requirements-dev.in
	${VIRTUALENV_ROOT}/bin/pip-compile requirements.in
	${VIRTUALENV_ROOT}/bin/pip-compile requirements-dev.in

.PHONY: test
test: test-flake8 test-unit

.PHONY: test-flake8
test-flake8: virtualenv requirements-dev
	${VIRTUALENV_ROOT}/bin/flake8 .

.PHONY: test-unit
test-unit: virtualenv requirements-dev
	${VIRTUALENV_ROOT}/bin/py.test ${PYTEST_ARGS}

.PHONY: functional-tests
functional-tests: virtualenv requirements-dev
	./functional-tests/setup.sh
	${VIRTUALENV_ROOT}/bin/cram -v functional-tests/

.PHONY: docker-build
docker-build:
	$(if ${RELEASE_NAME},,$(eval export RELEASE_NAME=$(shell git describe)))
	@echo "Building a docker image for ${RELEASE_NAME}..."
	docker build -t digitalmarketplace/scripts --build-arg release_name=${RELEASE_NAME} .
	docker tag digitalmarketplace/scripts digitalmarketplace/scripts:${RELEASE_NAME}

.PHONY: docker-push
docker-push:
	$(if ${RELEASE_NAME},,$(eval export RELEASE_NAME=$(shell git describe)))
	docker push digitalmarketplace/scripts:${RELEASE_NAME}
