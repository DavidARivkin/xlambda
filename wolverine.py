import logging
import traceback
from typing import Dict

try:
    import unzip_requirements  # NOQA
except ImportError:
    pass

from xlibs import exc, response
from xlibs.wolverine import utils
from xlibs.wolverine.constants import REQUIRED_ARGS


logger = logging.getLogger()
logger.setLevel(logging.WARNING)


def handler(event: Dict, context: Dict) -> Dict:
    '''Wolverine Lambda entry point handler

    :arg event: (dict) event input received from the invoker/trigger
    :arg context: (dict) contextual data provided by the Lambda platform
    '''
    try:
        result = execute(
            options=event,
        )

        return response.build(
            status=200,
            data=result,
        )

    except Exception as error:
        logger.exception(error)

        response.build(
            status=500,
            error={
                'type': type(error).__name__,
                'description': str(error),
                'trace': traceback.format_exc(),
            },
            original_request=event,
        )


def execute(*, options):
    '''Execute a request received by the Wolverine Lambda'''
    is_request_valid, validation_msg = utils.validate_request(
        options=options,
        required_args=REQUIRED_ARGS,
    )

    if not is_request_valid:
        raise exc.XLambdaExceptionInvalidRequest(validation_msg)

    metrics, settings = utils.get_lambda_info(
        function_name=options['name'],
        region=options['region'],
    )

    options['metrics'] = metrics
    options['settings'] = settings

    return options
