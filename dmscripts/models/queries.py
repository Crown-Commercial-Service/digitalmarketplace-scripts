import pandas as pd
import numpy as np


def successful_supplier_applications(brief_responses, briefs):
    brief_responses = brief_responses[brief_responses['essentialRequirements']]
    result = brief_responses.merge(briefs, left_on='briefId', right_on='id')

    return result[['briefId', 'lot', 'title', 'supplierId', 'supplierName', 'submittedAt']]


def briefs_with_summary_application_data(brief_responses, briefs):
    result = briefs.merge(brief_responses, left_on='id', right_on='briefId')
    group_cols = ['briefId', 'lot', 'title', 'status', 'essentialRequirements']
    counted = result[group_cols].groupby(group_cols).agg(np.size).reset_index()
    counted.columns.values[-1] = 'number of applications'
    return counted
