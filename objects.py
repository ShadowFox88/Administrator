import datetime
from collections.abc import Callable


class Operation(object):
    def __init__(self, function: Callable, symbol: str):
        self._function = function
        self.symbol = symbol

    def __call__(self, *args, **kwargs):
        return self._function(*args, **kwargs)


class MST(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(hours=-7)

    def dst(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return "-06:00"
