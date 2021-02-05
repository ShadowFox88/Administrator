from discord.ext import commands

from base import cogs


class ErrorHandler(cogs.ErrorHandler):
    def __init__(self, bot):
        super().__init__(bot)

        self.messages = {
            commands.MissingRequiredArgument: "{error_str}"
        }
        self.errors = tuple(self.messages.keys())

    async def output(self, error, destination):
        error_str = str(error)

        if isinstance(error, self.errors):
            message = self.messages[type(error)]
        else:
            message = self.format_exception(error)
        formatted = message.format(error_str=error_str.capitalize())
        await destination.send(formatted)


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
