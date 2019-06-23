'''Constant values that are common to all X-Lambdas'''
import os


# Basic settings
DEFAULT_STAGE = 'dev'
DEFAULT_REGION = 'us-east-1'
STAGE = os.environ.get('STAGE', DEFAULT_STAGE)
REGION = os.environ.get('REGION', DEFAULT_REGION)

# Miscellaneous
BASE_FUNCTION_NAME = 'xlambda-{function}-{stage}'

# Forecasting
CONFIDENCE_LEVEL = 0.9
FORECAST_TIMEFRAME = 3  # How many periods of 5 minutes to forecast
