'''Utility functions for the Wolverine Lambda'''
import datetime
import math
from typing import Dict, List, Optional

from xlibs import exc
from xlibs.utils import *  # NOQA
from xlibs.wolverine import aws_api_wrapper, constants


def get_lambda_info(*, function_name: str, region: str) -> List:
    '''Get demand metrics from a given Lamdba functions'''
    now = datetime.datetime.utcnow()
    start_time = now - datetime.timedelta(days=constants.METRICS_DAYS_AGO)

    status, metrics = aws_api_wrapper.get_metric_data(
        function_name=function_name,
        region_name=region,
        period=constants.METRICS_TIME_PERIOD,
        start_time=start_time,
        end_time=now,
        max_datapoints=constants.METRICS_MAX_DATAPOINTS,
    )

    if status != 200:
        raise exc.XLambdaExceptionGetMetricsFailed()

    status, settings = aws_api_wrapper.get_settings(
        function_name=function_name,
        region=region,
    )

    if status != 200:
        raise exc.XLambdaExceptionGetSettingsFailed()

    return (
        stringify_metrics_datetime(metrics=metrics),
        format_settings(settings=settings),
    )


def stringify_metrics_datetime(*, metrics: List) -> List:
    '''Stringify datetime objects in metrics retrieved from CloudWatch'''
    return {
        metric['timestamp'].strftime('%Y-%m-%d %H:%M:%S'): metric['value']
        for metric in metrics
    }


def format_settings(*, settings: Dict) -> Dict:
    '''Format Lambda settings'''
    formatted = {
        'runtime': normalize_runtime(aws_runtime=settings['Runtime']),
        'memory_size': settings['MemorySize'],
        'timeout': settings['Timeout'] * 1000,  # Convdrt to milliseconds
        'is_in_vpc': len(settings['VpcConfig']['VpcId']) > 0,
    }

    formatted['startup_time'] = estimate_startup_time(**formatted)

    return formatted


def estimate_startup_time(
        *,
        runtime: str,
        memory_size: int,
        is_in_vpc: Optional[bool] = False,
        **kwargs,
        ) -> int:
    '''Estimate how long it should take for a function to cold start'''
    coeff = constants.STARTUP_TIME.get(runtime)

    if not coeff:
        return constants.STARTUP_TIME['default']['startup_time']

    memory_ln = math.log(int(memory_size))

    estimate = math.ceil(math.exp(coeff['intercept'] + coeff['x'] * memory_ln))

    if is_in_vpc:
        estimate += constants.STARTUP_TIME['default']['vpc_overhead']

    return estimate


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
