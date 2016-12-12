# -*- coding: utf-8 -*-
"""Class used to output a framework master csv."""
from collections import OrderedDict
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


class GenerateMasterCSV(GenerateCSVFromAPI):
    """"Generate a master csv given a framework."""

    static_fieldnames = ('supplier_id', 'supplier_dm_name', 'application_status', 'declaration_status')
    service_status_labels = OrderedDict([
        ("not-submitted", "draft"),
        ("submitted", "completed")
    ])

    def __init__(self, client, target_framework_slug):
        """Set up CSV builder with a client, framework and lot details and a placeholder for output.

        :param client: Instance of dmapiclient.data.DataAPIClient
        :param target_framework_slug: A framework slug ie 'digital-outcomes-and-specialists-2' or 'g-cloud-8'
        """
        super(GenerateMasterCSV, self).__init__(client)
        self.target_framework_slug = target_framework_slug
        self.framework = self.client.get_framework(target_framework_slug)['frameworks']
        self.lot_slugs = tuple(i['slug'] for i in self.framework['lots'])

    def get_column_name(self, service_status, lot_slug):
        """For each lot we're working out how many submitted and non-submitted services they have.
        To indicate this in the csv we have headings like 'draft_iaas, completed_iaas, draft_saas, completed_saas etc.'
        In this method, given a status 'non-submitted' and a lot_slug 'iaas' we produce the label 'draft_iaas'.
        """
        return self.service_status_labels[service_status] + '_' + lot_slug

    def _get_dynamic_field_names(self):
        """
        :return: List of strings. Dynamic field names for CSV.
        """
        dynamic_fields = []
        for lot_name in self.lot_slugs:
            for label_prefix in self.service_status_labels.keys():
                dynamic_fields.append(self.get_column_name(label_prefix, lot_name))
        return dynamic_fields

    def get_fieldnames(self):
        """
        :return: List of strings. All field names for CSV.
        """
        return self.static_fieldnames + tuple(self._get_dynamic_field_names())

    def populate_output(self):
        """Method to actually populate our output placeholder."""
        self._update_with_supplier_data(self.output)

    def get_supplier_service_data(self, supplier_id):
        """Given a supplier ID return a list of dictionaries for services related to framework."""
        return self.client.find_draft_services_iter(supplier_id, framework=self.target_framework_slug)

    def get_supplier_frameworks(self):
        """Return supplier frameworks."""
        return self.client.find_framework_suppliers(self.target_framework_slug)['supplierFrameworks']

    def _update_with_supplier_data(self, output):
        """Update self.output with supplier data."""
        supplier_frameworks = self.get_supplier_frameworks()
        field_names = self.get_fieldnames()
        for sf in supplier_frameworks:
            # This bit takes care of the columns in static_fieldnames.
            supplier_id = sf['supplierId']
            declaration = sf['declaration']['status'] if sf['declaration'] else ''
            supplier_info = [supplier_id, sf['supplierName'], '', declaration]
            # This creates placeholders for the dynamic lot fieldnames.
            lot_placeholders = [0 for i in self._get_dynamic_field_names()]
            supplier_dict = dict(zip(field_names, supplier_info + lot_placeholders))
            # Get service data and process dynamic lot values
            service_data = self.get_supplier_service_data(supplier_id)
            for service in service_data:
                # Calculate the status of each service an what lot it is in then +1 to the corresponding column.
                column_name = self.get_column_name(service['status'], service['lotSlug'])
                supplier_dict[column_name] += 1
            output.append(supplier_dict)
