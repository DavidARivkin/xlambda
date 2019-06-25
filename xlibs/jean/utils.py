'''Utility functions for the Jean Lambda'''
import math
from typing import List

from xlibs.jean import constants

from statsmodels.tsa.holtwinters import SimpleExpSmoothing


def forecasting(*, metrics: List, timeframe: int) -> List:
    '''Estimate forecasting for Lambda container demand'''
    data = [metric['value'] for metric in metrics]

    model = SimpleExpSmoothing(endog=data)
    fitted_model = model.fit(**constants.EXP_SMOOTH_PARAMS)

    forecasts = fitted_model.predict(
        start=len(data),
        end=len(data) + timeframe - 1,
    )

    return [math.ceil(val) for val in forecasts]
