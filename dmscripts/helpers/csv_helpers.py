# -*- coding: utf-8 -*-
"""Base classes/ helpers for CSV creation."""
import collections
import os
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


class MultiCSVWriter(object):
    """Manage writing to multiple CSV files"""
    def __init__(self, output_dir, handlers):
        self.output_dir = output_dir
        self.handlers = handlers
        self._csv_writers = dict()
        self._csv_files = dict()
        self._counters = collections.Counter()

    def write_row(self, record):
        for handler in self.handlers:
            should_write = handler.should_write(record)
            if handler.matches(record) and should_write:
                self._counters.update([handler.NAME])
                row = handler.create_row(record)
                return self.csv_writer(handler, row).writerow(dict(row))
            elif not should_write:
                return self.csv_writer
        raise ValueError("record not handled by any handler")

    def csv_writer(self, handler, row):
        if handler.NAME not in self._csv_writers:
            fieldnames = [key for key, _ in row]
            self._csv_writers[handler.NAME] = csv.DictWriter(self._csv_files[handler.NAME], fieldnames=fieldnames)
            self._csv_writers[handler.NAME].writeheader()

        return self._csv_writers[handler.NAME]

    def csv_path(self, handler):
        return os.path.join(self.output_dir, handler.NAME + '.csv')

    def __enter__(self):
        for handler in self.handlers:
            self._csv_files[handler.NAME] = open(self.csv_path(handler), 'w+')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for f in self._csv_files.values():
            f.close()

    def print_counts(self):
        print(" ".join("{}={}".format(handler.NAME, self._counters[handler.NAME]) for handler in self.handlers))


def make_fields_from_content_questions(questions, record):
    return [
        field
        for question in questions
        for field in _make_fields_from_content_question(question, record)
        ]


def _make_fields_from_content_question(question, record):
    if question["type"] == "checkboxes":
        for option in question.options:
            # Make a CSV column for each label
            yield (
                make_field_title(question.id, option["label"]),
                count_field_in_record(question.id, option["label"], record)
            )
    elif question.fields:
        for field_id in sorted(question.fields.values()):
            # Make a CSV column containing all values
            yield (
                field_id,
                "|".join(service.get(field_id, "") for service in record["services"])
            )
    else:
        yield (
            question["id"],
            "|".join(str(service.get(question["id"], "")) for service in record["services"])
        )


def make_field_title(field_id, field_label):
    return "{} {}".format(field_id, field_label)


def count_field_in_record(field_id, field_label, record):
    return sum(1
               for service in record["services"]
               if field_label in service.get(field_id, []))


def write_csv(records, make_row, filename):
    """Write a list of records out to CSV"""
    def fieldnames(row):
        return [field[0] for field in row]

    writer = None

    with open(filename, "w+") as f:
        for record in records:
            sys.stdout.write(".")
            sys.stdout.flush()
            row = make_row(record)
            if writer is None:
                writer = csv.DictWriter(f, fieldnames=fieldnames(row))
                writer.writeheader()
            writer.writerow(dict(row))
