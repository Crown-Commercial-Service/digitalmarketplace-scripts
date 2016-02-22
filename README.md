# digitalmarketplace-scripts

This repository contains scripts that interact with the Digital Marketplace APIs (
[data API](https://github.com/alphagov/digitalmarketplace-api) and
[search-api](https://github.com/alphagov/digitalmarketplace-search-api)).

* `scripts/generate-user-email-list.py`
  script for generating a CSV of user email addresses and
  details in the Digital Marketplace.

* `scripts/index-services.py`
  Reads services from the API endpoint and writes to search-api for indexing.

* `scripts/generate-framework-agreement-data.py`
  Generates a tab-separated values file with the data required by CCS to populate
  the G-Cloud 7 framework agreements.  It uses the collated data from declaration
  and lot csv files generated by existing scripts in the API project: 
  `generate_lots_export_for_ccs_sourcing` and 
  `generate_declarations_export_for_ccs_sourcing`.

* `scripts/insert-framework-results.py`
  Reads a csv file of results for suppliers who have/have not been accepted onto
  a framework and posts to the API to set the `on_framework` value in the 
  `supplier_frameworks` table.
