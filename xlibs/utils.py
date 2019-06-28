'''Common utility functions for X-Lambdas'''
import json
from typing import Dict, List, Optional

import boto3
import yaml

from xlibs import constants


def validate_request(options: Dict, required_args: List) -> tuple:
    '''Validate a request received by a Lambda function'''
    if not all([arg in options.keys() for arg in required_args]):
        required = '", "'.join(required_args)
        return False, f'Missing required option arguments: "{required}"'

    return True, 'Valid request'


def get_object_from_yaml(*, filename: str):
    '''Retrieve a Python object from a YAML file'''
    with open(filename, 'r') as file:
        obj = yaml.load(file.read(), Loader=yaml.FullLoader)

    return obj


def get_function_name(*, function: str, stage: Optional[str] = None) -> str:
    '''Get function name from serverless yaml file'''
    if not stage:
        stage = constants.STAGE

    return constants.BASE_FUNCTION_NAME.format(
        function=function,
        stage=stage,
    )


def invoke_lambda(
        *,
        function: str,
        region: str,
        invocation_type: str,
        payload: Dict,
        log_type: str = 'None',
        ):
    '''Invokes a Lambda function

    Uses a separate boto3 session for each request to make it thread-safe

    :param function: name of the function to invoke
    :param invocation_type: one of these options:
        'RequestResponse': synchronous call, will wait for Lambda processing
        'Event': asynchronous call, will NOT wait for Lambda processing
        'DryRun': validate param values and user permission
    :param payload: payload data to submit to the Lambda function
    :param log_type: one of these options:
        'None': does not include execution logs in the response
        'Tail': includes execution logs in the response
    '''
    session = boto3.session.Session()
    aws_lambda = session.client('lambda')

    response = aws_lambda.invoke(
        FunctionName=function,
        InvocationType=invocation_type,
        LogType=log_type,
        Payload=json.dumps(payload),
    )

    # Decode response payload
    try:
        payload = response['Payload'].read(amt=None).decode('utf-8')
        response['Payload'] = json.loads(payload)

    except json.decoder.JSONDecodeError:
        response['Payload'] = None

    return response


def split_list(*, list_: List, n: int):
    '''Split a list into multiple lists

    :arg list_: original list to split up
    :arg n: size of each sublist
    '''
    for i in range(0, len(list_), n):
        yield list_[i:i + n]
