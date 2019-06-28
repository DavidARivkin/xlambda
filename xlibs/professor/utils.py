from typing import Dict

from xlibs import exc
from xlibs.utils import *  # NOQA
from xlibs.utils import get_object_from_yaml
from xlibs.professor import config, constants


def get_config(*, action: str) -> Dict:
    '''Get configuration parameters for running the Warming process'''
    try:
        config_obj = get_object_from_yaml(filename=constants.CONFIG_FILENAME)

        return config.XLambdaConfig(
            action=action,
            options=config_obj,
        )

    except Exception as error:
        load_config_exception = exc.XLambdaExceptionLoadConfigFailed(
            'Could not load the warming configuration options'
        )

        raise load_config_exception from error
