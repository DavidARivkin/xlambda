'''Wrapper functions to interact with AWS API endpoints'''
import datetime

import boto3


def get_metric_data(
        *,
        function_name: str,
        region_name: str,
        period: int,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        max_datapoints: int,
        ) -> tuple:
    '''Retrieve metric data from CloudWatch API'''
    client = boto3.client('cloudwatch', region_name=region_name)

    response = client.get_metric_data(
        MetricDataQueries=[
            {
                'Id': 'lambda_metrics',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/Lambda',
                        'MetricName': 'ConcurrentExecutions',
                        'Dimensions': [
                            {
                                'Name': 'FunctionName',
                                'Value': function_name,
                            },
                        ],
                    },
                    'Period': period,
                    'Stat': 'Maximum',
                },
                'ReturnData': True,
            },
        ],
        StartTime=start_time,
        EndTime=end_time,
        # NextToken='string',
        ScanBy='TimestampAscending',
        MaxDatapoints=max_datapoints,
    )

    status = response['ResponseMetadata']['HTTPStatusCode']
    metrics = [
        {
            'timestamp': response['MetricDataResults'][0]['Timestamps'][i],
            'value': int(response['MetricDataResults'][0]['Values'][i]),
        }
        for i in range(0, len(response['MetricDataResults'][0]['Timestamps']))
    ]

    return status, metrics


def get_settings(*, function_name: str, region: str) -> tuple:
    '''Get Lambda settings'''
    client = boto3.client('lambda', region_name=region)

    response = client.get_function_configuration(
        FunctionName=function_name,
    )

    status = response['ResponseMetadata']['HTTPStatusCode']

    return status, response
