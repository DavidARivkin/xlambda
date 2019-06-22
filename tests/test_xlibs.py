'''Test xlibs'''
import unittest
from unittest.mock import (
    patch,
)
from xlibs.response import build
from xlibs.utils import (
    get_object_from_s3,
)


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
        get_object_from_s3(
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
