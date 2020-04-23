# digitalmarketplace-scripts

![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)

## A short overview of current scripts

The `scripts` folder in this repository contains scripts that interact with the Digital Marketplace APIs (
[data API](https://github.com/alphagov/digitalmarketplace-api) and
[search-api](https://github.com/alphagov/digitalmarketplace-search-api)).

* `framework-applications/bulk-upload-documents.py`

  Script for uploading framework result letters and agreement signature pages.

* `export-dos-labs.py`, `export-dos-outcomes.py`, `export-dos-participants.py`, `export-dos-specialists.py`

  Scripts to extract CSV reports about all draft services submitted to a Digital Ouctcomes and Specialists style
  framework, generally to be run after applications have closed and supplier pass/fails have been set in the database.

* `export-framework-applicant-details.py`

   Extracts the "about you" data for all suppliers who applied to a framework, to enable CCS to get in touch with
   suppliers when they need to.

* `export-framework-results-reasons.py`

  To be run when a framework closes for applications - produces three CSV files for pass, fail and discretionary
  results, with relevant data to be passed to CCS. To exclude fake suppliers use the -e parameter with the IDs
  separated by commas (without spaces, e.g. -e 123,456,789). There is a list of known fake supplier IDs encrypted in 
  the private repository.

* `generate-buyer-email-list.py`

  Generates a list of buyer users name and email address, optionally with a list of their requirements.

* `generate-framework-agreement-signature-pages.py` and `generate-framework-agreement-counterpart-signature-pages.py`

  Scripts used to generate framework agreement page PDF files from the template in
  https://github.com/alphagov/digitalmarketplace-agreements

* `generate-framework-master-csv.py`

  To be run when a framework closes for applications - extracts a CSV report of all suppliers who expressed an interest
  in the framework and their eventual application status (did they make an application, only fill in the declaration,
  how many services submitted/left in draft per lot, etc). To exclude fake suppliers use the -e parameter with the IDs
  separated by commas (without spaces, e.g. -e 123,456,789). There is a list of known fake supplier IDs encrypted in 
  the private repository.

* `generate-g8-agreement-signature-pages.py` and `generate-g8-counterpart-signature-pages.py`

  **LEGACY** scripts used to generate framework agreement page PDF files for G-Cloud 8 from the template in
  https://github.com/alphagov/digitalmarketplace-agreements - saved for now because we may still need to re-generate some of
  these.

* `generate-questions-csv.py`

  Script that generates a CSV file for the supplier declaration and questions in the 'edit submission' manifest (i.e.
  service questions) for a given framework.

* `get-model-data.py`

  Iterate through one or more models and dump the data into a CSV according to supplied config.

* `get-user.py`

  Outputs details of a random active unlocked user with a given role.

* `index-to-search-service.py`
  **Runs nightly on Jenkins**. Reads services or briefs from the API endpoint and writes to search-api for indexing.

* `insert-framework-results.py`
  Reads a csv file of results for suppliers who have/have not been accepted onto
  a framework and posts to the API to set the `on_framework` value in the
  `supplier_frameworks` table.

* `publish-dos-draft-services.py`
  For a DOS-style framework (with no documents to migrate) this will make draft services for suppliers "on framework"
  into real services.

* `publish-g-cloud-draft-services.py`
  For a G-Cloud-style framework (with documents to migrate) this will make draft services for suppliers "on framework"
  into real services.

* `mark-definite-framework-results.py`

  Marks suppliers as having passed/failed a framework, where the result can be determined "automatically" not requiring
  human involvement (i.e. not "discretionary" results). To exclude fake suppliers use the --excluded-supplier-ids with 
  the IDs separated by commas (without spaces, e.g. --excluded-supplier-ids=123,456,789). There is a list of known 
  fake supplier IDs encrypted in the private repository.

* `notify-buyers-to-award-closed-briefs.py`

  **Runs nightly on Jenkins**. Send email notifications to buyer users reminding them to award their closed requirements.

* `notify-buyers-when-requirements-close.py`

  **Runs nightly on Jenkins**. Send email notifications to buyer users about closed requirements.

* `notify-successful-suppliers-for-framework.py`

  Email suppliers who have at least one successful lot entry on the given framework. Should be run once per framework,
  at the beginning of the standstill period when results from CCS are delivered to suppliers.

* `notify-suppliers-of-new-questions-answers.py`

  **Runs every morning on Jenkins.** If a buyer has posted a new question/answer on a brief in the last 24 hours, send an email to any
  suppliers who have started an application, completed an application or asked a question about the
  opportunity. If a supplier is interested in more than one brief that has had a question or answer posted,
  then these are grouped into a single email.

* `framework-applications/scan-g-cloud-services-for-bad-words.py`

  Checks all free-text fields in G-Cloud services for "bad words" and generates a CSV report of any bad words found.

* `send-dos-opportunities-email.py`

  **Runs Mon-Fri 8:00am on Jenkins**. Send emails with new opportunities on a lot to suppliers who are on this lot.

* `send-stats-to-performance-platform.py`

  Fetches application statistics for a framework from the API and pushes them to the Performance Platform.

* `update-framework-results.py`

  Sets supplier "on framework" status to a specified value for all supplier IDs read from file.

* `upload-counterpart-agreemets.py`

  Script used to upload countersigned/counterpart agreement PDFs to S3. This **MUST** be used rather than
  `bulk-upload-documents.py` because the "countersigned agreement path" needs to be set in the DB at the same time as
  the file is uploaded.

* `update-index-alias.py`

  Makes it easier for humans and computers (namely Jenkins) to update the alias of an elasticsearch index. It was written to assist with indexing services after migrating data between environments periodically with Jenkins.

* `virus-scan-s3-bucket.py`

  Runs a virus scan utilising a provided clamd (ClamAV) backend against a given S3 bucket, optionally restricting by path prefix and last modified datetime.

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

## Licence

Unless stated otherwise, the codebase is released under [the MIT License][mit].
This covers both the codebase and any sample code in the documentation.

The documentation is [&copy; Crown copyright][copyright] and available under the terms
of the [Open Government 3.0][ogl] licence.

[mit]: LICENCE
[copyright]: http://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/uk-government-licensing-framework/crown-copyright/
[ogl]: http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/
