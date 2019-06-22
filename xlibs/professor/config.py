import copy
from typing import (
    Dict,
)
from xlibs import (
    exc,
)


class XLambdaConfig():

    def __init__(self, options: Dict):
        self.options = self.validate_options(options=copy.deepcopy(options))

    @property
    def default(self):
        return self.options['default']

    @property
    def functions(self):
        return self.options['lambda_functions']

    @property
    def lambda_functions(self):
        return self.functions

    def validate_options(self, options: Dict) -> Dict:
        if 'default' not in options:
            options['default'] = {}

        options['default'] = self.fill_default(default=options['default'])

        if 'lambda_functions' not in options:
            raise exc.XLambdaExceptionConfigValidationFailed(
                'Config option \'lambda_functions\' is missing.'
            )

        if type(options['default']) is not dict:
            raise exc.XLambdaExceptionConfigValidationFailed(
                f"Config 'default' is of type {type(options['default'])}, "
                "expected Dict."
            )

        functions = options['lambda_functions']

        if type(functions) is not list:
            raise exc.XLambdaExceptionConfigValidationFailed(
                "Config 'lambda_functions' is of type "
                f"{type(options['lambda_functions'])}, expected List."
            )

        if len(functions) == 0:
            raise exc.XLambdaExceptionConfigValidationFailed(
                'Config "lambda_functions" list is empty.'
            )

        if not all([type(lambda_f) is dict for lambda_f in functions]):
            raise exc.XLambdaExceptionConfigValidationFailed(
                'Config "lambda_functions" must be a list of dictionaries.'
            )

        if not all([type('name' in lambda_f) for lambda_f in functions]):
            raise exc.XLambdaExceptionConfigValidationFailed(
                'Missing \'name\' attribute for one or more Lambdas in '
                'Config "lambda_functions" list.'
            )

        if not all([type('region' in lambda_f) for lambda_f in functions]):
            raise exc.XLambdaExceptionConfigValidationFailed(
                'Missing \'region\' attribute for one or more Lambdas in '
                'Config "lambda_functions" list.'
            )

        return options

    def fill_default(self, default: Dict) -> Dict:
        '''Fill default config dict with missing options that are mandatory

        :arg default: default options provided in the original config dict
        '''
        return default
