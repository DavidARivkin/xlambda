import logging
import traceback
from typing import Dict

from xlibs import exc, response
from xlibs.jean import constants, utils


logger = logging.getLogger()
logger.setLevel(logging.WARNING)


def handler(event: Dict, context: Dict) -> Dict:
    '''Jean Lambda entry point handler

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


def execute(*, options: Dict) -> Dict:
    '''Execute a request received by the Jean Lambda'''
    is_request_valid, validation_msg = utils.validate_request(
        options=options,
        required_args=constants.REQUIRED_ARGS,
    )

    if not is_request_valid:
        raise exc.XLambdaExceptionInvalidRequest(validation_msg)

    options['forecast'] = utils.forecasting(
        metrics=options['metrics'],
        timeframe=options['timeframe'],
    )

    return options
