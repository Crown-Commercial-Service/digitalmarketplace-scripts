# Digital Marketplace Scripts

![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)

Contains:
 - scripts used by Jenkins (either as scheduled tasks or one-off jobs)
 - scripts for framework lifecycle tasks (found in `/scripts/framework-applications`)
 - scripts for local developer use (e.g. `scripts/api-clients.shell.py`)
 - one-off scripts, stored for posterity (found in `/scripts/oneoff`)

Scripts in this repository are written in either Python or bash.

## Running scripts with Docker

One way to run common scripts locally without setting up dependencies is to use the pre-built
Docker image. If you have Docker set up, you can use `docker pull digitalmarketplace/scripts` to
download the latest image version. Then you can run any of the scripts with:

```
docker run digitalmarketplace/scripts scripts/... [options]
```

`docker run digitalmarketplace/scripts` without an explicit command will display the Python version,
release tag the container was built from and a list of available scripts.

If the script is connecting to any local apps/services you need to forward the ports to the docker
container. The easiest way to do this is to use `--net=host` argument for `docker run`:

```
docker run --net=host digitalmarketplace/scripts scripts/index-to-search-service.py services dev ...
```

This won't work however if you are running Docker for Mac; instead, see [below](#docker-for-mac-workaround).

If the script is generating output files you need to map a local directory to the output directory
in the container using a volume:

```
docker run --user $(id -u) --volume $(pwd)/data:/app/data digitalmarketplace/scripts scripts/get-model-data.py ...
```

### Docker for Mac workaround

If you are running in Docker on macOS and have local apps/services then `--net=host` will not work for you.
Instead, a workaround script has been provided that runs inside the container to forward the scripts to the
Docker host. To use it, run Docker like this:

```
docker run --entrypoint docker_for_mac_entrypoint.sh digitalmarketplace/scripts scripts/index-to-search-service.py dev ...
```

## Testing

Run the full test suite:

```
make test
```

To only run the Python tests:

```
make test-unit
```

To run the `flake8` linter:

```
make test-flake8
```

### Updating Python dependencies

`requirements.txt` file is generated from the `requirements.in` in order to pin
versions of all nested dependencies. If `requirements.in` has been changed (or
we want to update the unpinned nested dependencies) `requirements.txt` should be
regenerated with

```
make freeze-requirements
```

`requirements.txt` should be committed alongside `requirements.in` changes.

## Contributing

This repository is maintained by the Digital Marketplace team at the [Government Digital Service](https://github.com/alphagov).

If you have a suggestion for improvement, please raise an issue on this repo.

## Licence

Unless stated otherwise, the codebase is released under [the MIT License][mit].
This covers both the codebase and any sample code in the documentation.

The documentation is [&copy; Crown copyright][copyright] and available under the terms
of the [Open Government 3.0][ogl] licence.

[mit]: LICENCE
[copyright]: http://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/uk-government-licensing-framework/crown-copyright/
[ogl]: http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/
