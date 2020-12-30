import discord
from discord.ext import commands

from base import custom


class Administrator(custom.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or(">>>"),
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=">>>help and pings"
            ),
            allowed_mentions=discord.AllowedMentions(
                everyone=False,
                roles=False
            )
        )
        self._edit_cache = {}
        self.home_id = 464446709146320897

        exclude = ["base.cogs.error_handler"]  # noqa
        self.load_extensions("./cogs")

    @property
    def home(self):
        return self.get_guild(self.home_id)


if __name__ == '__main__':
    Administrator().run()
