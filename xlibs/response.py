'''Build responses for X-Lambdas'''
from typing import (
    Dict,
    Optional,
)


def build(
        *,
        status: int,
        msg: str = None,
        data: Optional[Dict] = None,
        error: Optional[Dict] = None,
        original_request: Optional[Dict] = None,
        ):
    '''Build response objects for X-Lambda

    :arg status: status to provide the response with
    :arg msg: any message
    :arg data: anything to be returned to the requester
    :arg error: details about an error
    :arg original_request: original event payload received by the Lambda
    '''
    return {
        'status': status,
        'msg': msg,
        'data': data,
        'error': error,
        'original_request': original_request,
    }
