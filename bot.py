import discord

import database
from base import custom


class Administrator(custom.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=">>>help and pings"
            ),
            allowed_mentions=discord.AllowedMentions(
                everyone=False,
                roles=False
            ),
            home=464446709146320897,
            max_edit_messages=1000,
            autocomplete=True
        )

        self.db = database.create(bot=self, config=self.config)

        self.load_base_extensions()
        self.load_extensions("cogs")


if __name__ == '__main__':
    Administrator().run()
