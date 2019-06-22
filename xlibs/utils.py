'''Common utility functions for X-Lambdas'''
import boto3


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
