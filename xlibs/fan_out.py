'''Fan out tasks to multiple workers'''
from typing import (
    List,
)


def to_wolverine(*, lambda_functions: List) -> List:
    '''Fan out warming jobs to Wolverine Lambda

    :arg lambda_functions: a list of Lambda functions to warm up
    '''
    return lambda_functions
