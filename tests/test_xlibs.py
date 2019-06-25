'''Test xlibs'''
from typing import Dict
import unittest
from unittest.mock import patch

from xlibs import constants, mutant, utils
from xlibs.response import build


class TestResponse(unittest.TestCase):
    '''Test the response routine'''

    def test_build_simple(self):
        '''Test the build function with a simplified response'''
        r = build(
            status=200,
        )

        self.assertIsInstance(r, dict)

        # Test response dict keys
        self.assertIn('status', r.keys())
        self.assertIn('msg', r.keys())
        self.assertIn('data', r.keys())
        self.assertIn('error', r.keys())
        self.assertIn('original_request', r.keys())

        # Test response dict values
        self.assertEqual(r['status'], 200)
        self.assertIsNone(r['msg'])
        self.assertIsNone(r['data'])
        self.assertIsNone(r['error'])
        self.assertIsNone(r['original_request'])

    def test_build_full(self):
        '''Test a response with all attributes'''
        msg = 'There\'s so much more to you than you know, not just pain and anger.'  # NOQA

        original_request = {
            'Waitress': 'Are you drinking to forget?',
            'Wolverine': 'No, I\'m drinking to remember.',
        }

        error = {
            'Clothing': 'Should not heal with Wolverine\'s body.',
        }

        r = build(
            status=200,
            msg=msg,
            data={'professor': 'Charles Xavier'},
            error=error,
            original_request=original_request,
        )

        self.assertEqual(r['msg'], msg)
        self.assertIsInstance(r['data'], dict)
        self.assertIn('professor', r['data'])
        self.assertEqual(r['data']['professor'], 'Charles Xavier')
        self.assertEqual(r['error'], error)
        self.assertEqual(r['original_request'], original_request)


class TestUtils(unittest.TestCase):
    '''Test utility functions'''

    @patch('xlibs.utils.boto3')
    def test_get_object_from_s3(self, boto3):
        '''Test function that gets objects from S3 storage'''
        utils.get_object_from_s3(
            bucket='x-mansion',
            object_key='Xavier School',
        )

        boto3.session.Session.assert_called()

        client = boto3.session.Session().client
        client.assert_called_with('s3')

        s3 = client()

        s3.get_object.assert_called()
        s3.get_object.assert_called_with(
            Bucket='x-mansion',
            Key='Xavier School',
        )

    def test_get_function_name(self):
        '''Test script that gets a function name from serverless.yml'''
        function_name = utils.get_function_name(function='wolverine')

        self.assertEqual(function_name, f'xlambda-wolverine-{constants.STAGE}')


class TestMutants(unittest.TestCase):
    '''Test Mutant classes'''

    @patch('xlibs.mutant.async_lambda')
    def test_execute(self, async_lambda):
        '''Test execution of Lambda invocations'''
        requests = [
            {'function_name': 'test1', 'payload': {'foo': 'bar'}},
            {'function_name': 'test2', 'payload': {'foo': 'bar'}},
            {'function_name': 'test3', 'payload': {'foo': 'bar'}},
            {'function_name': 'test4', 'payload': {'foo': 'bar'}},
            {'function_name': 'test5', 'payload': {'foo': 'bar'}},
        ]

        mutant_obj = mutant.Mutant()

        mutant_obj.execute(requests=requests)

        async_lambda.invoke_all.assert_called()
        async_lambda.invoke_all.assert_called_with(
            requests=requests,
            region=constants.REGION,
        )

    def test_cyclops_container_count(self):
        '''Test counting of how many containers should be warmed up'''
        target = {
            'name': 'Charles-Xavier',
            'region': 'us-east-1',
            'settings': {},
            'forecast': [4, 15, 2],
            'scaling': None,
        }

        cyclops = mutant.Cyclops()
        cyclops.aim(target=target)

        cyclops._target.scaling = get_scaling(1, 10, 50)
        self.assertEqual(cyclops.containers_to_warm, 10)

        cyclops._target.scaling = get_scaling(1, 20, 50)
        self.assertEqual(cyclops.containers_to_warm, 15)

        cyclops._target.scaling = get_scaling(1, 20, 8)
        self.assertEqual(cyclops.containers_to_warm, 8)


def get_scaling(
        min_containers: int = 1,
        max_containers: int = 10,
        max_concurrency: int = 50,
        ) -> Dict:
    return dict(
        zip(
            ['min_containers', 'max_containers', 'max_concurrency'],
            [min_containers, max_containers, max_concurrency],
        )
    )
