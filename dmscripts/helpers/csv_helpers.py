# -*- coding: utf-8 -*-
"""Base classes/ helpers for CSV creation."""
import sys

if sys.version_info > (3, 0):
    import csv
else:
    import unicodecsv as csv


class GenerateCSVFromAPI(object):
    """Stub class for master csv generation."""

    def __init__(self, client):
        self.client = client
        self.output = []

    def get_fieldnames(self):
        raise NotImplementedError("Required: Method for getting fieldnames.")

    def populate_output(self):
        """Generally you should populate self.output here."""
        raise NotImplementedError("Required: Method for populating output.")

    def write_csv(self, outfile=None):
        """Write CSV header from get_fieldnames and contents from self.output."""
        outfile = outfile or sys.stdout
        writer = csv.DictWriter(outfile, lineterminator="\n", fieldnames=self.get_fieldnames())

        writer.writeheader()
        for row in self.output:
            writer.writerow(row)
