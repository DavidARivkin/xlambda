import logging
import traceback
from typing import Dict

from xlibs import response, exc
from xlibs.professor import action_mapper, constants, utils


logger = logging.getLogger()
logger.setLevel(logging.WARNING)


def handler(event: Dict, context: Dict) -> Dict:
    '''Entry point for starting the Lambda Warming process

    :arg event: (dict) event input received from the invoker/trigger
    :arg context: (dict) contextual data provided by the Lambda platform
    '''
    try:
        result = execute(options=event)

        return response.build(
            status=200,
            data=result,
        )

    except Exception as error:
        logger.exception(error)

        return response.build(
            status=500,
            msg='Oops, something went wrong!',
            error={
                'type': type(error).__name__,
                'description': str(error),
                'trace': traceback.format_exc(),
            },
            original_request=event,
        )


def execute(*, options: Dict) -> Dict:
    '''Execute a request received by the Professor Lambda
    '''
    is_request_valid, validation_msg = utils.validate_request(
        options=options,
        required_args=constants.REQUIRED_ARGS,
    )

    if not is_request_valid:
        raise exc.XLambdaExceptionInvalidRequest(validation_msg)

    # Load the configuration params
    config = utils.get_config(action=options['action'])

    action_executor = action_mapper.get_executor(action=config.action)

    results = action_executor.run(config=config)

    return results
