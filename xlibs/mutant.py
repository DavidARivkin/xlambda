'''Mutant Classes'''
from typing import Dict, List, Optional

from xlibs import async_lambda
from xlibs.utils import get_function_name
from xlibs.professor import constants


class Mutant():
    '''Boilerplate for a Mutant class representing a Lambda worker'''

    def __init__(self, *args, **kwargs):
        self._name = None
        self._function_name = None

    @property
    def function_name(self) -> str:
        if not self._function_name:
            self._function_name = get_function_name(function=self._name)

        return self._function_name

    def execute(self, requests: List, region: Optional[str] = None) -> List:
        '''Invoke a Mutant Lambda'''
        if not region:
            region = constants.REGION

        return async_lambda.invoke_all(
            requests=requests,
            region=region,
        )


class Wolverine(Mutant):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._name = 'wolverine'

    def get_metrics(self, functions: List) -> List:
        '''Get metrics from CloudWatch'''
        requests = [
            {
                'function_name': self.function_name,
                'payload': function,
            }
            for function in functions
        ]

        response = self.execute(requests=requests)

        return [
            payload['data']
            for payload in response
            if payload['status'] == 200
        ]


class Jean(Mutant):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._name = 'jean'

    def forecast(self, functions_metrics: List, timeframe: int) -> List:
        '''Forecast future demand for a list of Lambda functions'''
        requests = [
            {
                'function_name': self.function_name,
                'payload': {**function, **{'timeframe': timeframe}},
            }
            for function in functions_metrics
        ]

        response = self.execute(requests=requests)

        return [
            payload['data']
            for payload in response
            if payload['status'] == 200
        ]


class Cyclops(Mutant):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._name = 'cyclops'
        self._target = None
        self._results = None

    @property
    def results(self):
        return self._results

    @property
    def containers_to_warm(self):
        '''Calculate number of containers to warm up'''
        forecast = max(self._target.forecast)
        min_containers = self._target.scaling['min_containers']
        max_containers = min(
            self._target.scaling['max_containers'],
            self._target.scaling['max_concurrency'],
        )

        return min(
            max(forecast, min_containers),
            max_containers,
        )

    def burn(self, functions_demand: List) -> List:
        '''Warm up a list of Lambdas'''
        requests = [
            {
                'function_name': self.function_name,
                'payload': function,
            }
            for function in functions_demand
        ]

        response = self.execute(requests=requests)

        return [
            payload['data']
            for payload in response
            if payload['status'] == 200
        ]

    def aim(self, target: Dict):
        '''Set a Lambda and its settings as target for the Cyclops laser'''
        self._target = CyclopsTarget(**target)

        return self

    def fire(self):
        '''Activate Cyclops laser on the target Lambda'''
        self._results = []

        requests = [
            {
                'function_name': self.target.name,
                'payload': self.target.payload,
            }
            for i in range(0, self.containers_to_warm)
        ]

        self._results = self.execute(
            requests=requests,
            region=self.target.region,
        )

        return self


class CyclopsTarget():

    def __init__(
            self,
            name: str,
            region: str,
            settings: Dict,
            forecast: List,
            scaling: Dict,
            *args,
            **kwargs,
            ):
        self.name = name
        self.region = region
        self.settings = settings
        self.forecast = forecast
        self.scaling = scaling

    @property
    def payload(self):
        '''Provide target payload in dictionary format'''
        return {
            'xlambda': {
                'action': 'warm_up',
                'settings': self.settings,
            },
        }
