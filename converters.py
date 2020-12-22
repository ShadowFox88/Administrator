import operator

from discord.ext import commands

import enums
from objects import Operation


class Lowered(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            return argument.lower()
        except Exception:
            raise commands.BadArgument("WIP")


class TriggerConverter(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            return enums.Trigger[argument.upper()]
        except Exception:
            raise commands.BadArgument("WIP")


class OperationConverter(commands.Converter):
    OPERATORS = {
        "add": Operation(operator.add, "+"),
        "sub": Operation(operator.sub, "-"),
        "mul": Operation(operator.mul, "x"),
        "div": Operation(operator.floordiv, "÷")
    }

    async def convert(self, ctx, argument):
        argument = argument.lower()
        operator_found = self.OPERATORS.get(argument)

        if operator_found:
            return operator_found
        raise commands.BadArgument(f'unsupported operation: "{argument}"')


class Difficulty(commands.Converter):
    MIN = 0
    MAX = 20

    async def convert(self, ctx, argument) -> int:
        try:
            argument = int(argument)
        except Exception:
            raise commands.BadArgument(f'cannot convert "{argument}" to int')
        else:
            if argument < self.MIN:
                comparative = "lower"
                value = self.MIN
            elif argument > self.MAX:
                comparative = "higher"
                value = self.MAX
            else:
                return argument
            raise commands.BadArgument(f"{argument} is {comparative} than "
                                       f"{value}")
