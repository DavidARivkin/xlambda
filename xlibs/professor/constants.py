'''Constant values for Professor Lambda'''
from xlibs.constants import *  # NOQA


REQUIRED_ARGS = [
    's3_bucket',
    'config_obj_name'
]

DEFAULT_CONFIG = {
    'region': 'us-east-1',
    'scaling': {
        'max_concurrency': 50,
        'min_containers': 1,
        'max_containers': 50,
    },
}
