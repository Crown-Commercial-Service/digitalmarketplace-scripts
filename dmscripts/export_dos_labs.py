def append_contact_information_to_services(records, required_contact_fields):
    for record in records:
        all_contact_info = record['supplier']['contactInformation'][0]  # assumption made of one and only one record

        required_contact_info = {
            key: all_contact_info[key] for key in all_contact_info.keys() if key in required_contact_fields
        }

        record['services'] = [{**service, **required_contact_info} for service in record['services']]

    return records
