'''Common utility functions for X-Lambdas'''
import json
from typing import Dict, List, Optional
import boto3
import yaml
from xlibs import constants


def get_object_from_s3(
        *,
        bucket: str,
        object_key: str,
        encoding: str = 'utf-8',
        ) -> str:
    '''Get an object from S3 and provide its contents

    :arg bucket: name of the bucket where the object is saved
    :arg object_key: key name of the object
    :arg encoding: character encoding - defaults to utf-8
    :arg client: boto3 S3 client
    :return: the object contents
    '''
    session = boto3.session.Session()
    s3 = session.client('s3')

    response = s3.get_object(
        Bucket=bucket,
        Key=object_key,
    )

    return response['Body'].read(amt=None).decode(encoding)


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
