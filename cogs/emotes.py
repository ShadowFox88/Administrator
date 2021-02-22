import asyncio
import re
from typing import Tuple

import discord
from discord.ext import commands

from base import custom


class Emotes(custom.Cog):
    def __init__(self, bot):
        self.bot = bot

        self._cached = set()
        self._cached_event = asyncio.Event()
        self.emotes = {}
        self.pattern = re.compile(r";(?P<escaped>\\)?(?P<name>[a-zA-Z0-9_]+)")
        self.bonk_emotes: Tuple = None

        self.bot.loop.create_task(self.__ainit__())

    async def __ainit__(self):
        await self.bot.wait_until_ready()
        self._cache_emotes(self.bot.home)

        for guild in self.bot.guilds:
            self._cache_emotes(guild)

        self.bonk_emotes = (self.emotes["angery"], "🗞️")
        self._cached_event.set()

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    def _cache_emotes(self, guild):
        if guild.id not in self._cached:
            self._cached.add(guild.id)

            for emote in guild.emojis:
                self.emotes.setdefault(emote.name, str(emote))

    @commands.Cog.listener()
    async def on_message(self, message):
        ctx = await self.bot.get_context(message)

        if not self._cached_event.is_set() or message.author.bot or ctx.valid:
            return
        generated = wrapping = ""
        matches = self.pattern.findall(message.content)

        if not matches:
            return

        for escaped, name in matches:
            emote_found = self.emotes.get(name)

            if not emote_found:
                continue
            append = emote_found

            if escaped:
                wrapping += f"{append} "
                continue
            elif not escaped and wrapping:
                append = f"`{wrapping}` {append} "
                wrapping = ""
            generated += append

        if wrapping:
            generated += f"`{wrapping}`"

        if not generated:
            return
        elif len(generated) > 2000:
            return await message.add_reaction("❌")
        await message.channel.send(generated)

    @commands.command()
    async def bonk(self, ctx, message: discord.Message):
        joined = ("").join(self.bonk_emotes)

        for emote in self.bonk_emotes:
            await message.add_reaction(emote)
        await ctx.send(f"{message.author.mention} {joined}")


def setup(bot):
    bot.add_cog(Emotes(bot))
