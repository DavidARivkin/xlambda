'''Test Professor'''
import copy
import json
import unittest
from unittest.mock import (
    MagicMock,
    patch,
)
import professor
from xlibs import (
    exc,
)
from xlibs.professor import (
    constants,
)
from xlibs.professor.utils import (
    execute,
    validate_request,
    get_config,
)
from xlibs.professor.config import (
    XLambdaConfig,
)


DUMMY_JSON = '{"Charles": "Xavier"}'


class CustomMock():
    '''Produces custom Mock objects for tests'''

    def validate_request_return_true():
        return MagicMock(return_value=(True, None))

    def validate_request_return_false():
        return MagicMock(return_value=(False, 'Some validation error msg'))

    def get_object_from_s3_dummy_json_str():
        return MagicMock(return_value=DUMMY_JSON)

    def get_object_from_s3_dummy_non_json_str():
        return MagicMock(return_value='This is not a JSON string')


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
            options=json.loads(DUMMY_JSON),
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

        self.full_default = {}

    def test_config(self):
        '''Test the config object'''
        options = {
            'default': self.default,
            'lambda_functions': self.functions,
        }

        config = XLambdaConfig(options=options)

        self.assertEqual(config.default, self.default)
        self.assertEqual(config.functions, self.functions)

    def test_config_missing_default(self):
        '''Test config object missing default options'''
        options = {
            'lambda_functions': self.functions,
        }

        config = XLambdaConfig(options=options)

        self.assertEqual(config.default, self.full_default)
        self.assertEqual(config.functions, self.functions)

    def test_config_broken_options(self):
        '''Test the config object with broken options'''
        pass
