def supplier_applications(brief_responses, briefs):
    result = brief_responses.merge(briefs, left_on='briefId', right_on='id')

    return result[['submittedAt', 'briefId', 'lot', 'title', 'supplierName']]
