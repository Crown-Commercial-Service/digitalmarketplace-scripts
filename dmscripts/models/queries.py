def successful_supplier_applications(brief_responses, briefs):
    brief_responses = brief_responses[brief_responses['essentialRequirements'] == True]
    result = brief_responses.merge(briefs, left_on='briefId', right_on='id')

    return result[['briefId', 'lot', 'title', 'supplierId', 'supplierName', 'submittedAt']]
