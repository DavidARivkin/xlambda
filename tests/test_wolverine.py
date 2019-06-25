'''Test Wolverine'''
import unittest

from xlibs.wolverine import utils


class TestWolverineUtils(unittest.TestCase):
    '''Test Wolverine utility functions'''

    def test_estimate_startup_time(self):
        '''Test the startup time estimation logic'''
        test_cases = {
            'csharp': {
                '128': 5031,
                '256': 3214,
                '512': 2054,
                '1024': 1312,
                '1536': 1010,
                '3008': 654,
            },
            'java': {
                '128': 5018,
                '256': 2617,
                '512': 1365,
                '1024': 712,
                '1536': 487,
                '3008': 259,
            },
            'nodejs': {
                '128': 77,
                '256': 30,
                '512': 12,
                '1024': 5,
                '1536': 3,
                '3008': 2,
            },
            'python': {
                '128': 26,
                '256': 17,
                '512': 12,
                '1024': 8,
                '1536': 6,
                '3008': 4,
            },
        }

        for runtime, estimates in test_cases.items():
            for memory_size, expected in estimates.items():
                estimate = utils.estimate_startup_time(
                    runtime=runtime,
                    memory_size=int(memory_size),
                )
                self.assertEqual(estimate, expected)
