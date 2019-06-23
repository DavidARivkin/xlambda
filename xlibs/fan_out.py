'''Fan out tasks to multiple workers'''
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import (
    Dict,
    List,
)
from xlibs.utils import (
    invoke_lambda,
)


class FanOut():
    '''Fan out warming jobs to a Lambda function'''

    def __init__(self, *args, **kwargs):
        self._loop = None
        self._results = []

    @property
    def results(self):
        return self._results

    def run(self, worker, action, payloads):
        '''Execute the fan out routine'''
        self._loop = asyncio.get_event_loop()

        tasks = [
            {
                'executor': getattr(worker, action),
                'payload': payload,
            }
            for payload in payloads
        ]

        self._loop.run_until_complete(
            self.process_tasks(tasks=tasks)
        )

        self._loop.close()

    async def process_tasks(self, tasks):
        '''Convert tasks to Lambda invocations and execute them'''
        invocations = [
            task['executor'](payload=task['payload'])
            for task in tasks
        ]

        for response in asyncio.as_completed(invocations):
            await response

            self._responses.append(response)

    async def execute(self, task: Dict) -> Dict:
        '''Execute a task'''
        # Need a wrapper to pass keyword arguments to invoke lambda function
        def invoke_wrapper(*args, **kwargs):
            return invoke_lambda(
                function=self.lambda_name,
                region=task['region'],
                invocation_type='RequestResponse',
                payload=task,
            )

        with ThreadPoolExecutor(1) as executor:
            await self.loop.run_in_executor(executor, invoke_wrapper)
