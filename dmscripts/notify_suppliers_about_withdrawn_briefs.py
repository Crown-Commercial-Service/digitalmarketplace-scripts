import dmapiclient
from datetime import datetime, date, timedelta

def main():
    briefs_withdrawn_on = date.today() - timedelta(days=1)
    dmapiclient.DataAPIClient.find_briefs_by_status_datestamp("withdrawn_at", briefs_withdrawn_on, briefs_withdrawn_on, inclusive=True)
    return True
