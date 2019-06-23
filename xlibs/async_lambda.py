import asyncio
from aiohttp import ClientSession
from typing import Dict

from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.session import Session

from urllib.parse import urlparse
from os.path import join
from json import dumps


creds = Session().get_credentials()
LAMBDA_ENDPOINT_BASE = 'https://lambda.{region}.amazonaws.com/2015-03-31/functions'  # NOQA


def create_signed_headers(*, url: str, payload: Dict):
    '''Sign AWS API request headers'''
    host_segments = urlparse(url).netloc.split('.')
    service = host_segments[0]
    region = host_segments[1]

    request = AWSRequest(
        method='POST',
        url=url,
        data=dumps(payload),
    )

    SigV4Auth(creds, service, region).add_auth(request)

    return dict(request.headers.items())


async def invoke(*, url: str, payload: Dict, session):
    signed_headers = create_signed_headers(url=url, payload=payload)

    async with session.post(url,
                            json=payload,
                            headers=signed_headers) as response:
        return await response.json()


def generate_invocations(*, requests, base_url, session):
    for request in requests:
        url = join(base_url, request['function_name'], 'invocations')
        yield invoke(url=url, payload=request['payload'], session=session)


def invoke_all(*, requests, region='us-east-1'):
    base_url = LAMBDA_ENDPOINT_BASE.format(region=region)

    async def wrapped():
        async with ClientSession(raise_for_status=True) as session:
                invocations = generate_invocations(
                    requests=requests,
                    base_url=base_url,
                    session=session,
                )

                return await asyncio.gather(*invocations)

    return asyncio.get_event_loop().run_until_complete(wrapped())
