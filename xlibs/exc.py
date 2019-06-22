'''Custom exceptions for X-Lambdas'''


class XLambdaExceptionInvalidRequest(Exception):
    '''Invalid request received by an X-Lambda through event object'''
    pass


class XLambdaExceptionLoadConfigFailed(Exception):
    '''Failed to load configuration parameters for the warming process'''
    pass


class XLambdaExceptionConfigValidationFailed(Exception):
    '''Failed to validate configuration options'''
    pass
