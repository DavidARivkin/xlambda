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


class XLambdaExceptionFanOutError(Exception):
    '''Failed to load name of the function to execute fan out jobs'''
    pass


class XLambdaExceptionExhaustedWarmBatches(Exception):
    '''Exhausted available warming batches

    Use in loop: professor.start_warming.prepare_warm_batches
    '''
    pass
