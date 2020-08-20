import boto3
import json
import os
import uuid


class LogRetriever(object):
    """
    Encapsulates the log retrieval process.
    To fetch all log events of a know stream use get_log_events.
    To fetch all log events from multiple streams within a date range,
    use get_log_event_in_epoch_range.
    All log events will be written as JSON files in a user-supplied directory.
    """
    def __init__(self, arn, group):
        self.group = group
        # create session for the log client
        sts_client = boto3.client('sts')
        session_name = str(uuid.uuid4())
        sts_response = sts_client.assume_role(
            RoleArn=arn,
            RoleSessionName=session_name
        )
        session = boto3.session.Session(
            aws_access_key_id=sts_response['Credentials']['AccessKeyId'],
            aws_secret_access_key=sts_response['Credentials']['SecretAccessKey'],
            aws_session_token=sts_response['Credentials']['SessionToken'],
            region_name='eu-west-1'
        )
        self.client = session.client('logs')

    def filter_streams_in_interval(self, streams, earliest_epoch, latest_epoch):
        """
        Parses all the stream object of boto's describe_log_streams,
        filtering out those without any entries in the desired interval
        """
        filtered_streams = []
        for stream in streams:
            # covert javascript/AWS milliseconds to python/ISO seconds
            stream['firstEventTimestamp'] /= 1000
            stream['lastEventTimestamp'] /= 1000
            # append the UUID of the log in the interval
            if earliest_epoch < stream['lastEventTimestamp'] and stream['firstEventTimestamp'] < latest_epoch:
                filtered_streams.append(stream['logStreamName'])
        return filtered_streams

    def describe_log_streams(self, earliest_epoch, latest_epoch):
        streams = []
        # fetch first log stream
        response = self.client.describe_log_streams(
            logGroupName=self.group,
            orderBy='LastEventTime',
            descending=True
        )
        # check epoch range and add stream logStreamName
        streams.extend(self.filter_streams_in_interval(response['logStreams'], earliest_epoch, latest_epoch))
        while len(response['logStreams']) > 0 and 'nextToken' in response.keys():
            response = self.client.describe_log_streams(
                logGroupName=self.group,
                orderBy='LastEventTime',
                descending=True,
                nextToken=response['nextToken']
            )
            # check epoch range and add stream logStreamName
            streams.extend(self.filter_streams_in_interval(response['logStreams'], earliest_epoch, latest_epoch))
        return streams

    def get_log_events(self, stream, directory):
        """
        see example use in ./scripts/oneoff/get-log-events.py
        """
        print(f'Fetching {stream} stream.')
        counter = 0
        directory = os.path.join(directory, self.group, stream)
        os.makedirs(directory, exist_ok=True)
        # fetch the logs first page
        response = self.client.get_log_events(
            logGroupName=self.group,
            logStreamName=f'{stream}',
            startFromHead=True
        )
        with open(f'{directory}/{counter}.json', 'w') as f:
            json.dump(response, f)
        # iterate to fetch the rest of the pages
        while len(response['events']) > 0:
            counter += 1
            response = self.client.get_log_events(
                logGroupName=self.group,
                logStreamName=stream,
                startFromHead=True,
                nextToken=response['nextForwardToken']
            )
            with open(f'{directory}/{counter}.json', 'w') as f:
                json.dump(response, f)
        return counter + 1

    def get_log_event_in_epoch_range(self, directory, earliest_epoch, latest_epoch):
        """
        Example to retrieve all log events in <cloud-watch-log-group> from 2019-05-20:
        lr = LogRetriever('<arn-with-access-to=cloud-watch>', '<cloud-watch-log-group>')
        lr.get_log_event_in_epoch_range(
            '/local/directory/to/write/log/events',
            int(datetime.datetime(2019,5,20,0,0,0).timestamp()),
            int(datetime.datetime(2019,5,20,23,59,59).timestamp())
        )
        """
        # get all streams in range
        streams = self.describe_log_streams(earliest_epoch, latest_epoch)
        print(f'Found {len(streams)} streams with log events in the requested interval.')
        for stream in streams:
            # write log events in directory
            self.get_log_events(stream, directory)
