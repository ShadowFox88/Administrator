import datetime
import enum
from collections.abc import Callable

from discord.ext import commands


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


class Trigger(enum.Enum):
    IN = 0
    OUT = 1

    @classmethod()
    async def convert(cls, ctx, argument):
        try:
            return cls[argument.upper()]
        except KeyError:
            raise commands.BadArgument(f"Invalid trigger given: {argument}")
