import functools

__version_info__ = ('0', '0', '1')
__version__ = '.'.join(__version_info__)


def memoize(func):
    cache = {}

    @functools.wraps(func)
    def memoized(*args):
        try:
            return cache[args]
        except KeyError:
            cache[args] = func(*args)
            return cache[args]
    return memoized