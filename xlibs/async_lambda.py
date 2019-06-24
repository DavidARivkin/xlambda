import asyncio
import json
import os
from typing import Dict, List
import urllib

import aiohttp
from botocore import session, awsrequest, auth

from xlibs import constants


AWS_CREDENTIALS = session.Session().get_credentials()


def sign_headers(*, url: str, payload: Dict):
    '''Sign AWS API request headers'''
    host_segments = urllib.parse.urlparse(url).netloc.split('.')
    service = host_segments[0]
    region = host_segments[1]

    request = awsrequest.AWSRequest(
        method='POST',
        url=url,
        data=json.dumps(payload),
    )

    auth.SigV4Auth(AWS_CREDENTIALS, service, region).add_auth(request)

    return dict(request.headers.items())


async def invoke(*, url: str, payload: Dict, session):
    '''Invoke a Lambda function'''
    signed_headers = sign_headers(url=url, payload=payload)

    async with session.post(url, json=payload, headers=signed_headers) \
            as response:
        return await response.json()


def generate_invocations(*, requests: List, base_url: str, session):
    for request in requests:
        url = os.path.join(base_url, request['function_name'], 'invocations')

        yield invoke(url=url, payload=request['payload'], session=session)


def invoke_all(*, requests: List, region: str = 'us-east-1'):
    base_url = constants.LAMBDA_ENDPOINT.format(region=region)

    async def wrapper():
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            invocations = generate_invocations(
                requests=requests,
                base_url=base_url,
                session=session,
            )

            return await asyncio.gather(*invocations)

    loop = asyncio.get_event_loop()

    return loop.run_until_complete(wrapper())
