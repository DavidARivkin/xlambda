'''Map Professor actions to execution functions'''
from xlibs import exc
from xlibs.professor import start_warming


ACTION_MAP = {
    'warm_up': start_warming,
}


def get_executor(*, action: str):
    try:
        return ACTION_MAP[action]

    except KeyError as error:
        raise exc.XLambdaExceptionInvalidRequest(
            f'Action "{action}" is not recognized, expected: '
            f'{", ".join(ACTION_MAP.keys())}.'
        ) from error
