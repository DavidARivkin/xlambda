'''Start the execution of the Lambda warming process'''
from typing import Dict, List

from xlibs import constants, exc, mutant, utils


def run(*, config: Dict) -> Dict:
    '''Run the Lambda warming process

    :arg config: validated configuration options loaded from S3
    '''
    functions = prepare_functions(config=config)

    return [
        result
        for batch in utils.split_list(
            list_=functions,
            n=config.max_concurrency,
        )
        for result in execute_batch(functions=batch, config=config)
    ]


def execute_batch(*, functions: List, config) -> List:
    '''Execute a batch of Lambdas

    :arg functions: a batch of Lambda functions to warm up
    :arg config: validated configuration options loaded from S3
    '''
    # Get metrics from CloudWatch
    wolverine = mutant.Wolverine()
    functions = wolverine.get_metrics(functions=functions)

    # Run predictions for how many containers should be warmed up
    jean = mutant.Jean()
    functions = jean.forecast(
        functions_metrics=functions,
        timeframe=constants.FORECAST_TIMEFRAME,
    )

    # Prepare warm up batches (make sure we stay within max_concurrency limit)
    warm_batches = prepare_warm_batches(
        functions=functions,
        max_concurrency=config.max_concurrency,
    )

    # Warm up the containers
    cyclops = mutant.Cyclops()
    warm_results = [
        result
        for functions_batch in warm_batches
        for result in cyclops.burn(functions_demand=functions_batch)
    ]

    return {
        'warm_results': warm_results,
    }


def prepare_functions(*, config) -> List:
    '''Append default configuration parameters to a list of functions

    :arg config: validated configuration options loaded from S3
    '''
    return [
        {
            **config.default,
            **function
        }
        for function in config.functions
    ]


def prepare_warm_batches(*, functions: List, max_concurrency: int) -> List:
    '''Prepare batches of functions within the max concurrency limit'''
    batches = [{'sum': 0, 'functions': []}]

    for f in functions:
        demand_peak = max(f['forecast'])

        f['warm_count'] = min(
            demand_peak,
            max_concurrency,
            f['scaling']['max_containers'],
        )

        for batch in batches:
            try:
                if batch['sum'] + f['warm_count'] <= max_concurrency:
                    batch['functions'].append(f)
                    batch['sum'] += f['warm_count']
                    break

                raise exc.XLambdaExceptionExhaustedWarmBatches()

            except exc.XLambdaExceptionExhaustedWarmBatches:
                new_batch = {'sum': f['warm_count'], 'functions': [f]}
                batches.append(new_batch)
                break

    return [batch['functions'] for batch in batches]
