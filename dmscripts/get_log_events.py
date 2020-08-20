import boto3
import json
import os
import uuid


def get_log_events(
    arn,  # 'arn:aws:iam::161120766136:role/RoleName'
    group,  # 'prod-group-name'
    stream,  # '9e1b2784-39cc-5016-87c0-845e'
    directory  # '/Users/username/Downloads/test' must be absolute
):
    # create session
    sts_client = boto3.client('sts')
    session_name = str(uuid.uuid4())
    sts_response = sts_client.assume_role(
        RoleArn=arn,
        RoleSessionName=session_name
    )
    session = boto3.session.Session(
        aws_access_key_id=sts_response['Credentials']['AccessKeyId'],
        aws_secret_access_key=sts_response['Credentials']['SecretAccessKey'],
        aws_session_token=sts_response['Credentials']['SessionToken']
    )
    print(sts_response)

    counter = 0
    directory = os.path.join(directory, group, stream)
    os.makedirs(directory, exist_ok=True)
    print(directory)
    # fetch the logs first page
    logs_client = session.client('logs')
    logs_response = logs_client.get_log_events(
        logGroupName=group,
        logStreamName=f'{stream}',
        startFromHead=True
    )
    with open(f'{directory}/{counter}.json', 'w') as f:
        json.dump(logs_response, f)
        print(f'{directory}/{counter}.json')
    # iterate to fetch the rest of the pages
    while len(logs_response['events']) > 0:
        counter += 1
        logs_response = logs_client.get_log_events(
            logGroupName=group,
            logStreamName=stream,
            startFromHead=True,
            nextToken=logs_response['nextForwardToken']
        )
        with open(f'{directory}/{counter}.json', 'w') as f:
            json.dump(logs_response, f)
            print(f'{directory}/{counter}.json')
    return counter + 1
