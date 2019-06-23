'''Test Professor'''
import copy
import json
from typing import Optional, Dict
import unittest
from unittest.mock import MagicMock, patch
import professor
from xlibs import exc
from xlibs.professor import constants, start_warming
from xlibs.professor.utils import execute, validate_request, get_config
from xlibs.professor.config import XLambdaConfig


DUMMY_JSON_STR = '{"Charles": "Xavier"}'


class CustomMock():
    '''Produces custom Mock objects for tests'''

    def validate_request_return_true():
        return MagicMock(return_value=(True, None))

    def validate_request_return_false():
        return MagicMock(return_value=(False, 'Some validation error msg'))

    def get_object_from_s3_dummy_json_str():
        return MagicMock(return_value=DUMMY_JSON_STR)

    def get_object_from_s3_dummy_non_json_str():
        return MagicMock(return_value='This is not a JSON string')

    def dummy_prepare_warm_batches():
        warm_batches = [
            [{}, {}],  # Batch 1
            [{}, {}, {}],  # Batch 2
            [{}],  # Batch 3
        ]
        return MagicMock(return_value=warm_batches)


class TestProfessor(unittest.TestCase):
    '''Test the Professor Lambda'''

    @patch('professor.utils')
    def test_handler(self, utils):
        options = {'Mutants': 'X-Men'}
        context = {'House': 'of Gifted Youngsters'}

        response = professor.handler(options, context)

        utils.execute.assert_called()
        utils.execute.assert_called_with(
            options=options,
        )

        self.assertIsInstance(response, dict)


class TestProfessorUtils(unittest.TestCase):
    '''Test the professor utils lib'''

    @property
    def required(self):
        return copy.copy(constants.REQUIRED_ARGS)

    def test_validate_valid_request(self):
        '''Test request validation routine'''
        is_request_valid, validation_msg = validate_request(
            options={arg: 'whatever' for arg in self.required},
        )

        self.assertTrue(is_request_valid)

    def test_validate_broken_request(self):
        '''Test validation routine with a broken request'''
        is_request_valid, validation_msg = validate_request(
            options={arg: 'whatever' for arg in self.required[:-1]},
        )

        self.assertFalse(is_request_valid)
        self.assertIsInstance(validation_msg, str)

    @patch(
        'xlibs.professor.utils.validate_request',
        new_callable=CustomMock.validate_request_return_true)
    @patch('xlibs.professor.utils.get_config')
    @patch('xlibs.professor.utils.start_warming')
    def test_execute_valid_request(
            self,
            start_warming,
            get_config,
            validate_request,
            ):
        '''Test execution of a valid request'''
        options = {
            's3_bucket': 'x-men',
            'config_obj_name': 'x-lambda.yml',
        }

        execute(options=options)

        get_config.assert_called()
        get_config.assert_called_with(
            bucket=options['s3_bucket'],
            config_obj_name=options['config_obj_name'],
        )

        start_warming.run.assert_called()

    @patch(
        'xlibs.professor.utils.get_object_from_s3',
        new_callable=CustomMock.get_object_from_s3_dummy_json_str)
    @patch(
        'xlibs.professor.utils.validate_request',
        new_callable=CustomMock.validate_request_return_false)
    def test_execute_invalid_request(
            self,
            validate_request,
            get_object_from_s3
            ):
        '''Test execution of a valid request'''
        self.assertRaises(
            exc.XLambdaExceptionInvalidRequest,
            execute,
            options={},
        )

    @patch(
        'xlibs.professor.utils.get_object_from_s3',
        new_callable=CustomMock.get_object_from_s3_dummy_json_str)
    @patch('xlibs.professor.utils.config.XLambdaConfig')
    def test_get_config(self, XLambdaConfig, get_object_from_s3):
        get_config(
            bucket='foo',
            config_obj_name='bar',
        )

        XLambdaConfig.assert_called()
        XLambdaConfig.assert_called_with(
            options=json.loads(DUMMY_JSON_STR),
        )

    @patch(
        'xlibs.professor.utils.get_object_from_s3',
        new_callable=CustomMock.get_object_from_s3_dummy_non_json_str)
    def test_get_config_fails(self, get_object_from_s3):
        self.assertRaises(
            exc.XLambdaExceptionLoadConfigFailed,
            get_config,
            bucket='foo',
            config_obj_name='bar',
        )


class TestProfessorConfig(unittest.TestCase):
    '''Test the professor config lib'''

    def setUp(self):
        self.default = {
            'foo': 'bar',
        }

        self.functions = [
            {
                'name': 'x-men',
                'region': 'us-east-1',
            },
        ]

    def test_config(self):
        '''Test the config object'''
        options = {
            'default': self.default,
            'lambda_functions': self.functions,
        }

        config = XLambdaConfig(options=options)

        self.assertEqual(
            config.default,
            {**constants.DEFAULT_CONFIG, **self.default}
        )
        self.assertEqual(config.functions, self.functions)

    def test_config_missing_default(self):
        '''Test config object missing default options'''
        options = {
            'lambda_functions': self.functions,
        }

        config = XLambdaConfig(options=options)

        self.assertEqual(config.default, constants.DEFAULT_CONFIG)
        self.assertEqual(config.functions, self.functions)

    def test_config_broken_options(self):
        '''Test the config object with broken options'''
        pass


class TestStartWarming(unittest.TestCase):
    '''Test the start_warming scripts'''

    def setUp(self):
        self.config = XLambdaConfig(
            options={
                'default': {
                    'region': 'us-east-1',
                    'warm_payload': {'warm': True},
                    'max_concurrency': 2,
                },
                'lambda_functions': [
                    {
                        'name': 'x-men',
                    },
                    {
                        'name': 'starship',
                        'region': 'mars-crater-1',
                    }
                ],
            },
        )

    def test_prepare_functions(self):
        '''Test preparation of functions for the warming process'''
        functions = start_warming.prepare_functions(config=self.config)

        self.assertIsInstance(functions, list)
        self.assertEqual(len(functions), 2)

        self.assertEqual(functions[0]['name'], 'x-men')
        self.assertEqual(functions[0]['region'], 'us-east-1')
        self.assertEqual(functions[1]['name'], 'starship')
        self.assertEqual(functions[1]['region'], 'mars-crater-1')

        for function in functions:
            keys = function.keys()
            self.assertIn('name', keys)
            self.assertIn('region', keys)
            self.assertIn('warm_payload', keys)
            self.assertIn('scaling', keys)

    def test_prepare_warm_batches(self):
        '''Test the prepare_warm_batches function'''
        functions = [
            {
                'name': 'A',
                'forecast': [
                    {'upper': 13},
                    {'upper': 12},
                    {'upper': 16},
                ],
                'scaling': {'max_containers': 10},
            },
            {
                'name': 'B',
                'forecast': [
                    {'upper': 6},
                    {'upper': 15},
                    {'upper': 9},
                ],
                'scaling': {'max_containers': 20},
            },
            {
                'name': 'C',
                'forecast': [
                    {'upper': 27},
                    {'upper': 34},
                    {'upper': 31},
                ],
                'scaling': {'max_containers': 50},
            },
            {
                'name': 'D',
                'forecast': [
                    {'upper': 2},
                    {'upper': 3},
                    {'upper': 5},
                ],
                'scaling': {'max_containers': 20},
            },
            {
                'name': 'E',
                'forecast': [
                    {'upper': 16},
                    {'upper': 21},
                    {'upper': 8},
                ],
                'scaling': {'max_containers': 50},
            },
        ]

        # Function A: 10 -> batch 1 (10)
        # Function B: 15 -> batch 1 (25)
        # Function C: 30 -> batch 2 (30)
        # Function D: 5  -> batch 1 (30)
        # Function E: 21 -> batch 3 (21)

        batches = start_warming.prepare_warm_batches(
            functions=functions,
            max_concurrency=30,
        )

        self.assertEqual(len(batches), 3)
        self.assertEqual(len(batches[0]), 3)
        self.assertEqual(len(batches[1]), 1)
        self.assertEqual(len(batches[2]), 1)

        self.assertEqual(batches[0][0]['name'], 'A')
        self.assertEqual(batches[0][1]['name'], 'B')
        self.assertEqual(batches[0][2]['name'], 'D')
        self.assertEqual(batches[1][0]['name'], 'C')
        self.assertEqual(batches[2][0]['name'], 'E')

    @patch('xlibs.professor.start_warming.execute_batch')
    def test_run(self, execute_batch):
        '''Test running the warming process'''
        functions = start_warming.prepare_functions(config=self.config)

        start_warming.run(config=self.config)

        execute_batch.assert_called()
        execute_batch.assert_called_with(
            functions=functions,
            config=self.config,
        )

    @patch('xlibs.professor.start_warming.mutant')
    @patch(
        'xlibs.professor.start_warming.prepare_warm_batches',
        new_callable=CustomMock.dummy_prepare_warm_batches)
    def test_execute_batch(self, prepare_warm_batches, mutant):
        '''Test execution of a batch of functions'''
        functions = start_warming.prepare_functions(config=self.config)

        start_warming.execute_batch(
            functions=functions,
            config=self.config,
        )

        mutant.Wolverine.assert_called()
        mutant.Wolverine().get_metrics.assert_called_with(
            functions=functions,
        )

        mutant.Jean.assert_called()
        mutant.Jean().forecast.assert_called_with(
            functions_metrics=mutant.Wolverine().get_metrics(),
            timeframe=constants.FORECAST_TIMEFRAME,
        )

        prepare_warm_batches.assert_called()
        prepare_warm_batches.assert_called_with(
            functions=mutant.Jean().forecast(),
            max_concurrency=self.config.max_concurrency,
        )

        mutant.Cyclops.assert_called()
        self.assertEqual(mutant.Cyclops().warm_up.call_count, 3)
