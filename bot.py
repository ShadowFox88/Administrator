from collections import OrderedDict
from os import environ
from typing import Dict

import discord
from discord.ext import commands

from base import custom

environ["JISHAKU_NO_UNDERSCORE"] = environ["JISHAKU_NO_DM_TRACEBACK"] = "True"


class Administrator(custom.Bot):
    def __init__(self, *args, **kwargs):
        _edit_cache_maximum = kwargs.pop("max_messages", 1000)

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
            max_messages=0
        )
        self._edit_cache_maximum = _edit_cache_maximum
        self._edit_cache: Dict[int, discord.Message] = OrderedDict()

        exclude = ["base.cogs.error_handler"]  # noqa: F841
        self.load_extensions("./cogs")

    def _get_edit_cached_message(self, message_id: int):
        message_found = self._edit_cache.get(message_id, None)

        if not message_found:
            if len(self._edit_cache) == self._edit_cache_maximum:
                self._edit_cache.popitem(last=False)
        return message_found


if __name__ == '__main__':
    Administrator().run()
