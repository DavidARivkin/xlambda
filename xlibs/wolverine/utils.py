'''Utility functions for the Wolverine Lambda'''
import datetime
import math
from typing import Dict, List

import boto3

from xlibs import exc
from xlibs.wolverine import constants


def validate_request(options: Dict) -> tuple:
    '''Validate a request received by the Professor Lambda
    '''
    if not all([arg in options.keys() for arg in constants.REQUIRED_ARGS]):
        required = '", "'.join(constants.REQUIRED_ARGS)
        return False, f'Missing required option arguments: "{required}"'

    return True, 'Valid request'


def get_lambda_info(*, function_name: str, region: str) -> List:
    '''Get demand metrics from a given Lamdba functions'''
    now = datetime.datetime.utcnow()
    start_time = now - datetime.timedelta(days=constants.METRICS_DAYS_AGO)

    status, metrics = get_metric_data(
        function_name=function_name,
        region_name=region,
        period=constants.METRICS_TIME_PERIOD,
        start_time=start_time,
        end_time=now,
        max_datapoints=constants.METRICS_MAX_DATAPOINTS,
    )

    if status != 200:
        raise exc.XLambdaExceptionFailedGetMetrics()

    status, settings = get_settings(
        function_name=function_name,
        region=region,
    )

    if status != 200:
        raise exc.XLambdaExceptionFailedGetSettings()

    return metrics, settings


def get_metric_data(
        *,
        function_name: str,
        region_name: str,
        period: int,
        start_time: int,
        end_time: int,
        max_datapoints: int,
        ) -> Dict:
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


def stringify_metrics_datetime(*, metrics: List) -> List:
    '''Stringify datetime objects in metrics retrieved from CloudWatch'''
    return {
        metric['timestamp'].strftime('%Y-%m-%d %H:%M:%S'): metric['value']
        for metric in metrics
    }


def get_settings(*, function_name: str, region: str) -> Dict:
    '''Get Lambda settings'''
    client = boto3.client('lambda', region_name=region)

    settings = client.get_function_configuration(
        FunctionName=function_name,
    )

    return settings


def format_settings(*, settings: Dict) -> Dict:
    '''Format Lambda settings'''
    return {
        'runtime': normalize_runtime(settings['Runtime']),
        'memory': settings['MemorySize'],
        'timeout': settings['Timeout'],
        'inside_vpc': len(settings['VpcConfig']['VpcId']) > 0,
    }


def estimate_startup_time(*, runtime: str, memory: int) -> int:
    '''Estimate how long it should take for a function to cold start'''
    coeff = constants.STARTUP_TIME_COEFFICIENT.get(runtime)

    if not coeff:
        return constants.STARTUP_TIME_COEFFICIENT['default']['startup_time']

    memory_ln = math.log(int(memory))

    return math.ceil(math.exp(coeff['intercept'] + coeff['x'] * memory_ln))


def normalize_runtime(*, aws_runtime: str) -> str:
    '''Normalize the runtimes'''
    runtime = aws_runtime.lower()

    if 'python' in runtime:
        return 'python'

    if 'java' in runtime:
        return 'java'

    if 'node' in runtime:
        return 'nodejs'

    if 'go' in runtime:
        return 'go'

    if 'dotnet' in runtime:
        return 'dotnet'

    if 'ruby' in runtime:
        return 'ruby'

    return 'unknown'
