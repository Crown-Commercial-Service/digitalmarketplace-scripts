"""Class used to output a framework master csv."""
import csv
from sys import stdout


class GenerateMasterCSV(object):
    """"Generate a master csv given a framework."""

    static_fieldnames = ['supplier_id', 'supplier_dm_name', 'application_status', 'declaration_status']
    lot_name_prefixes = ['draft', 'completed']

    def __init__(self, client, target_framework_slug):
        """Set up CSV builder with a client, framework and lot details and a placeholder for output.

        :param client: Instance of dmapiclient.data.DataAPIClient
        :param target_framework_slug: A framework slug ie 'digital-outcomes-and-specialists-2' or 'g-cloud-8'
        """
        self.client = client
        self.target_framework_slug = target_framework_slug
        self.framework = self.client.get_framework(target_framework_slug)['frameworks']
        self.lot_names = [i['slug'] for i in self.framework['lots']]
        self.output = []

    def _get_dynamic_field_names(self):
        """
        :return: List of strings. Dynamic field names for CSV.
        """
        dynamic_fields = []
        for lot_name in self.lot_names:
            for prefix in self.lot_name_prefixes:
                dynamic_fields.append('_'.join([prefix, lot_name]))
        return dynamic_fields

    def get_fieldnames(self):
        """
        :return: List of strings. All field names for CSV.
        """
        return self.static_fieldnames + self._get_dynamic_field_names()

    def populate_output(self):
        """Method to actually populate our output placeholder."""
        self._update_with_supplier_data(self.output)
        self._update_with_lot_data(self.output)

    def write_csv(self, outfile=None):
        """Write CSV header from get_fieldnames and contents from self.output."""
        outfile = outfile or stdout
        writer = csv.DictWriter(outfile, lineterminator="\n", fieldnames=self.get_fieldnames())

        writer.writeheader()
        for row in self.output:
            # Workaround to force unicode.
            writer.writerow({k: v.encode('utf8') for k, v in row.items()})

    def get_supplier_service_data(self, supplier_id):
        """Given a supplier ID return a list of dictionaries for services related to framework."""
        return self.client.find_draft_services_iter(supplier_id, framework=self.target_framework_slug)

    def _update_with_supplier_data(self, output):
        """Update self.output with supplier data."""
        supplier_frameworks = self.client.find_framework_suppliers(self.target_framework_slug)['supplierFrameworks']
        field_names = self.get_fieldnames()
        for sf in supplier_frameworks:
            declaration = sf['declaration']['status'] if sf['declaration'] else ''
            supplier_info = [sf['supplierId'], sf['supplierName'], '', declaration]
            lot_placeholders = [0 for i in self._get_dynamic_field_names()]
            output.append(dict(zip(field_names, supplier_info + lot_placeholders)))

    def _update_with_lot_data(self, output):
        """Update self.output with lot data."""
        for supplier_dict in output:
            service_data = self.get_supplier_service_data(supplier_dict['supplier_id'])
            for service in service_data:
                if service['status'] == 'submitted':
                    supplier_dict['completed_' + service['lot']] += 1
                elif service['status'] == 'not-submitted':
                    supplier_dict['draft_' + service['lot']] += 1
