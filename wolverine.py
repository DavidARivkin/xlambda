import logging
import traceback
from typing import Dict

from xlibs import exc, response
from xlibs.wolverine import constants, utils


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
        required_args=constants.REQUIRED_ARGS,
    )

    if not is_request_valid:
        raise exc.XLambdaExceptionInvalidRequest(validation_msg)

    metrics, settings = utils.get_lambda_info(
        function_name=options['name'],
        region=options['region'],
    )

    options['metrics'] = utils.stringify_metrics_datetime(metrics=metrics)
    options['settings'] = utils.format_settings(settings)

    return options
