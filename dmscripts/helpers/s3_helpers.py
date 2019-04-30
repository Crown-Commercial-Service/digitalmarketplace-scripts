
BUCKET_CATEGORIES = [
    'agreements',
    'communications',
    'documents',
    'submissions',
    'reports'
]


def get_bucket_name(stage, bucket_category):
    if bucket_category not in BUCKET_CATEGORIES:
        return None
    if stage in ['local', 'dev']:
        return "digitalmarketplace-dev-uploads"
    if stage not in ['preview', 'staging', 'production']:
        return None

    bucket_name = 'digitalmarketplace-{0}-{1}-{1}'.format(bucket_category, stage)
    print("BUCKET: {}".format(bucket_name))
    return bucket_name
