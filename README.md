# digitalmarketplace-scripts

## A short overview of current scripts

The `scripts` folder in this repository contains scripts that interact with the Digital Marketplace APIs (
[data API](https://github.com/alphagov/digitalmarketplace-api) and
[search-api](https://github.com/alphagov/digitalmarketplace-search-api)).

* `bulk-upload-ccs-documents.py`

  **LEGACY** script from when CCS used to send us zip files of documents to upload, saved for now just in case it
  might be of use again in future.

* `bulk-upload-documents.py`

  Script for uploading framework result letters and agreement signature pages.

* `export-dos-labs.py`, `export-dos-outcomes.py`, `export-dos-participants.py`, `export-dos-specialists.py`

  Scripts to extract CSV reports about all draft services submitted to a Digital Ouctcomes and Specialists style
  framework, generally to be run after applications have closed and supplier pass/fails have been set in the database.

* `export-framework-applicant-details.py`

   Extracts the "about you" data for all suppliers who applied to a framework, to enable CCS to get in touch with
   suppliers when they need to.

* `export-framework-results-reasons.py`

  To be run when a framework closes for applications - produces three CSV files for pass, fail and discretionary
  results, with relevant data to be passed to CCS.

* `generate-buyer-email-list.py`

  Generates a list of buyer users name and email address, optionally with a list of their requirements.

* `generate-framework-agreement-signature-pages.py` and `generate-framework-agreement-counterpart-signature-pages.py`

  Scripts used to generate framework agreement page PDF files from the template in
  https://github.gds/gds/digitalmarketplace-agreements

* `generate-framework-master-csv.py`

  To be run when a framework closes for applications - extracts a CSV report of all suppliers who expressed an interest
  in the framework and their eventual application status (did they make an application, only fill in the declaration,
  how many services submitted/left in draft per lot, etc.)

* `generate-g8-agreement-signature-pages.py` and `generate-g8-counterpart-signature-pages.py`

  **LEGACY** scripts used to generate framework agreement page PDF files for G-Cloud 8 from the template in
  https://github.gds/gds/digitalmarketplace-agreements - saved for now because we may still need to re-generate some of
  these.

* `generate-questions-csv.py`

  Script that generates a CSV file for the supplier declaration and questions in the 'edit submission' manifest (i.e.
  service questions) for a given framework.

* `get-model-data.py`

  Iterate through one or more models and dump the data into a CSV according to supplied config.

* `index-services.py`
  **Runs nightly on Jenkins**. Reads services from the API endpoint and writes to search-api for indexing.

* `insert-framework-results.py`
  Reads a csv file of results for suppliers who have/have not been accepted onto
  a framework and posts to the API to set the `on_framework` value in the
  `supplier_frameworks` table.

* `make-dos-live.py`
  For a DOS-style framework (with no documents to migrate) this will make draft services for suppliers "on framework"
  into real services.

* `make-g-cloud-live.py`
  For a G-Cloud-style framework (with documents to migrate) this will make draft services for suppliers "on framework"
  into real services.

* `mark-definite-framework-results.py`

  Marks suppliers as having passed/failed a framework, where the result can be determined "automatically" not requiring
  human involvement (i.e. not "discretionary" results).

* `notify-buyers-when-requirements-close.py`

  **Runs nightly on Jenkins**. Send email notifications to buyer users about closed requirements.

* `notify-successful-suppliers-for-framework.py`

  Email suppliers who have at least one successful lot entry on the given framework. Should be run once per framework,
  at the beginning of the standstill period when results from CCS are delivered to suppliers.

* `scan-g-cloud-drafts-for-bad-words.py`

  Checks all free-text fields in submitted G-Cloud draft services for "bad words" and generates a CSV report of any bad
  words found.

* `send-stats-to-performance-platform.py`

  Fetches application statistics for a framework from the API and pushes them to the Performance Platform.

* `set-search-alias.py`

  Used to set a new alias to an existing Elasticsearch index, via the Search API.

* `update-framework-results.py`

  Sets supplier "on framework" status to a specified value for all supplier IDs read from file.

* `upload-counterpart-agreemets.py`

  Script used to upload countersigned/counterpart agreement PDFs to S3. This **MUST** be used rather than
  `bulk-upload-documents.py` because the "countersigned agreement path" needs to be set in the DB at the same time as
  the file is uploaded.

## A general approach to writing new scripts

Historically (and currently), this respository has been filled with small files that slightly diverge from one another. The idea has been that scripts are written for things that happen once (slash infrequently) in the lifecycle of a framework -- so we write our script, run it once, and then walk away.

This is a good thing. It means we have a cleaner API and less code to maintain.

However, we've ended up with a lot of scripts doing similar things, so there has been an effort more recently to introduced some more general code to help make these behaviours
easier.

If you are writing a script that:

- iterates through all of something from the API (eg "get all buyer users")
- transforms specific values in your data collection (eg "get the domain name of user email addresses")
- merges data between two different models (eg "get number of draft briefs per buyer user")
- getting counts in one-to-many relationships (eg "get number of users per supplier")

then you should be *strongly biased* to using the following reusable code.

#### `modeltrawler.py`

Iterates through a set of models.
Returns only specified keys (including nested keys).
Default behaviour is to return all keys.

```python
mt = ModelTrawler('users', data_api_client)
mt.get_data(keys=('id', 'emailAddress', ('supplier', 'name'), 'role'))
data.to_csv(filename, index=False, encoding='utf-8')
```

CSV output
```csv
...
1,don@scdp.biz,Stanley Cooper Draper Price, supplier
2,andy@dm.info,Dunder Mifflin, supplier
3,paul@gov.uk,,buyer
...
```

#### ``queries.py``

This file contains the logic you need for joining files, as well as sorting, counting or processing values.

```python
# assumes `suppliers.csv` and `users.csv` exist in the `./data` directory
data = join(
    ({'model': 'suppliers', 'key': 'id'},
     {'model': 'users', 'key': "supplierId"}),
    './data'
)
data = data[('supplierId', 'name', 'dunsNumber', 'emailAddress')]
data.to_csv(filename, index=False, encoding='utf-8')
```

CSV output
```csv
...
101,Stanley Cooper Draper Price,123456789,don@scdp.biz
101,Stanley Cooper Draper Price,123456789,peggy@scdp.biz
102,Dunder Mifflin,111111119,andy@dm.info
...
```

#### `get-model-data.py`

We want to be able to write everything as config dictionaries and then run it all through the same generalised logic. The `get-model-data.py` script gives a good example of how to do this.
