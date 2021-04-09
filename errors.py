import inspect

from discord.ext.commands import CommandError


class WorksheetsError(CommandError):
    pass


class MissingRequiredArguments(CommandError):
    def __init__(self, number: int, *params: inspect.Parameter):
        joined = (", ").join(p.name for p in params)

        super().__init__(
            f"missing at least {number} required argument: {joined}"
        )
