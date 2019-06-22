'''Start the execution of the Lambda warming process'''
from typing import (
    Dict,
)
from xlibs import (
    fan_out,
)


def run(*, config: Dict) -> Dict:
    '''Run the Lambda warming process

    :arg config: validated configuration options loaded from S3
    '''
    # Fan-out warming jobs to the Wolverine Lambda
    results = fan_out.to_wolverine(
        default_config=config.default,
        lambda_functions=config.lambda_functions,
    )

    return {
        'warming_results': results,
    }
