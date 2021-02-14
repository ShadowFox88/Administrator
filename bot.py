import os

import discord
from discord.ext import commands

from base import custom

FLAGS = ("NO_UNDERSCORE", "NO_DM_TRACEBACK", "HIDE")

for flag in FLAGS:
    os.environ[f"JISHAKU_{flag}"] = "True"


class Administrator(custom.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(
            command_prefix=commands.when_mentioned_or(">>>"),
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=">>>help and pings"
            ),
            allowed_mentions=discord.AllowedMentions(
                everyone=False,
                roles=False
            ),
            home=464446709146320897,
            max_edit_messages=1000
        )

        self.load_base_extensions(exclude=["error_handler.py"])


if __name__ == '__main__':
    Administrator().run()
