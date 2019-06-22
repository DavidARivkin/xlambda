import logging
import traceback
from typing import (
    Dict,
)
from xlibs import (
    response,
)
from xlibs.professor import (
    utils,
)


logger = logging.getLogger()
logger.setLevel(logging.WARNING)


def handler(event: Dict, context: Dict) -> Dict:
    '''Entry point for starting the Lambda Warming process

    :arg event: (dict) event input received from the invoker/trigger
    :arg context: (dict) contextual variables provided by the Lambda platform
    '''
    try:
        result = utils.execute(
            options=event,
        )

        return response.build(
            status=200,
            msg=result.get('msg'),
            data=result.get('data'),
            original_request=event,
        )

    except Exception as error:
        logger.exception(error)

        response.build(
            status=500,
            msg='Oops, something went wrong!',
            error={
                'type': type(error).__name__,
                'description': str(error),
                'trace': traceback.format_exc(),
            },
            original_request=event,
        )
