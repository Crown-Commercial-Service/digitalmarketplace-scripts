# digitalmarketplace-scripts

This repository contains scripts that interact with the Digital Marketplace APIs (
[data API](https://github.com/alphagov/digitalmarketplace-api) and
[search-api](https://github.com/alphagov/digitalmarketplace-search-api)]).

* `scripts/generate-user-email-list.py`
  script for generating a CSV of user email addresses and
  details in the Digital Marketplace.

* `scripts/index-services.py`
  Reads services from the API endpoint and writes to search-api for indexing.

* `scripts/generate-framework-agreements.py`
  Generates populated PDF files of G-CLoud framework agreements using exported 
  declaration and lot csv files.

## Requirements

In order to run PDF-generating scripts you will need to install 
[PDFtk](https://www.pdflabs.com/tools/pdftk-server/).

