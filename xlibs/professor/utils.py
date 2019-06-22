import json
from typing import (
    Dict,
)
from xlibs.utils import *  # NOQA
from xlibs.utils import (
    get_object_from_s3,
)
from xlibs import (
    exc,
)
from xlibs.professor import (
    constants,
    start_warming,
    config,
)


def execute(*, options: Dict) -> Dict:
    '''Execute a request received by the Professor Lambda
    '''
    is_request_valid, validation_msg = validate_request(
        options=options,
    )

    if not is_request_valid:
        raise exc.XLambdaExceptionInvalidRequest(validation_msg)

    # Load the configuration params
    config = get_config(
        bucket=options['s3_bucket'],
        config_obj_name=options['config_obj_name'],
    )

    return start_warming.run(config=config)


def validate_request(options: Dict) -> tuple:
    '''Validate a request received by the Professor Lambda
    '''
    if not all([arg in options.keys() for arg in constants.REQUIRED_ARGS]):
        required = '", "'.join(constants.REQUIRED_ARGS)
        return False, f'Missing required option arguments: "{required}"'

    return True, 'Valid request'


def get_config(bucket: str, config_obj_name: str) -> Dict:
    '''Get configuration parameters for running the Warming process

    :arg bucket: name of the S3 bucket where configuration object is stored
    :arg config_obj_name: name of the configuration object in the S3 bucket
    '''
    try:
        raw_config = get_object_from_s3(
            bucket=bucket,
            object_key=config_obj_name,
        )

        return config.XLambdaConfig(options=json.loads(raw_config))

    except Exception as error:
        load_config_exception = exc.XLambdaExceptionLoadConfigFailed(
            'Could not load the warming configuration options'
        )

        raise load_config_exception from error
