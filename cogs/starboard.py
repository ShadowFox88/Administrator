import asyncio
import inspect
from collections.abc import Iterable
from typing import Optional

from discord.ext import commands, flags, menus

import errors
from base import custom, utils


class Starboard(custom.Cog):
    class Source(menus.ListPageSource):
        async def format_page(self, menus, entry):
            args, kwargs = entry

            return {
                "content": args[0],
                **kwargs
            }

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.guild.id == self.GUILD_ID

    @property
    def guild(self):
        return self.bot.get_guild(self.GUILD_ID)

    @property
    def starboard(self):
        return self.guild.get_channel(self.STARBOARD_ID)

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.bot.db.wait_until_ready()

        if message.channel == self.db.starboard:
            search = self.bot.STARRED_MESSAGE.search(message.content)

            await self.bot.db.add(message, search)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        if payload.channel_id == self.db.starboard.id:
            message = await self.db.starboard.fetch_message(payload.message_id)
            search = self.bot.STARRED_MESSAGE.search(message.content)
            params = map(int, search.group("stars", "id"))

            await self.bot.db.update(message.content, *params)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        if payload.channel_id == self.db.starboard.id:
            await self.bot.db.delete(payload.message_id)

    @flags.add_flag("--message", type=int)
    @flags.add_flag("--stars", type=int)
    @flags.add_flag("--channel", type=int)
    @flags.add_flag("--one", action="store_true")
    @flags.command(name="starboard")
    async def _starboard(self, ctx, id: Optional[int], **attrs):
        payloads_found: Iterable = None
        content = default = "❓ This message could not be found."
        args = []
        kwargs = {}
        one = attrs.pop("one")
        attrs = {k: v for k, v in attrs.items() if v}

        if id:
            attrs["id"] = id

        if not id and not attrs:
            command = self.bot.get_command("starboard")
            signature = inspect.signature(command.callback)
            parameters = list(signature.parameters.values())

            raise errors.MissingRequiredArguments(1, *parameters[2:])
        payloads_found = self.bot.db.get(one=one, **attrs)

        if payloads_found:
            if isinstance(payloads_found, Iterable):
                entries = []

                for index, payload in enumerate(payloads_found, start=1):
                    embed = payload.generate_embed()

                    entries.append(embed)
                source = self.Source(entries, per_page=1)
                menu = menus.MenuPages(
                    source=source,
                    timeout=60.0,
                    clear_reactions_after=True
                )

                return await menu.start(ctx)
            args, kwargs = await self.generate_entry(payloads_found)
            content = args[0]
        message = await ctx.send(content, **kwargs)

        if content != default:
            def check(reaction, user):
                return (user == ctx.author and
                        reaction.emoji == "🗑️" and
                        reaction.message == message)

            await message.add_reaction("🗑️")

            try:
                reaction, _ = await self.bot.wait_for(
                    "reaction_add",
                    check=check,
                    timeout=60.0
                )
            except asyncio.TimeoutError:
                await utils.clear_reactions(message)
            else:
                await message.delete()


def setup(bot):
    bot.add_cog(Starboard(bot))
