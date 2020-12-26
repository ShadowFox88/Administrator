import asyncio
import random
import re
from typing import Optional
from typing import Union

import discord
from discord.ext import commands

from base import custom
from converters import Difficulty


class Fun(custom.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.symbols = {
            "circle": "⏺️",
            "square": "⏹️",
            "triangle": "🔼",
            "arrow": "➡️"
        }
        self.flags = {
            "correct": "✅",
            "incorrect": "❌",
            "invalid": "❔"
        }
        self.space = re.compile(r" +")

    def _parse_response(self, message: str):
        response = []
        message = self.space.sub(" ", message.lower())

        for word in message.split():
            append = self.symbols.get(word, None)

            if append is None:
                append = word
            response.append(append)
        return response

    async def _get_webhook(self, channel: discord.TextChannel):
        webhooks = await channel.webhooks()
        webhook_found = discord.utils.get(
            webhooks,
            name="Administrator",
            user=self.bot.user
        )

        if not webhook_found:
            webhook_found = await channel.create_webhook(name="Administrator",
                                                         reason="Webhook init")
        return webhook_found

    def generate_answer(self, *, difficulty: int):
        answer = []
        # convert dict_values to be subscriptable for random.choice
        values = list(self.symbols.values())

        for _ in range(difficulty):
            answer.append(random.choice(values))
        return answer, ("").join(answer)

    def generate_check(self, ctx):
        return lambda m: m.channel == ctx.channel and m.author == ctx.author

    def verify_answer(self, response: str, answer: str):
        flags = ""
        message = ("").join(answer)
        values = list(self.symbols.values())
        response = self._parse_response(response)

        for i, symbol in enumerate(response):
            if symbol == answer[i]:
                key = "correct"
            elif symbol in values:
                key = "incorrect"
            else:
                key = "invalid"
            flags += self.flags[key]
        return (f"{message}\n"
                f"{flags}")

    @commands.command()
    async def memory(self, ctx, difficulty: Difficulty = 6):
        """
        WIP
        """
        answer, formatted = self.generate_answer(difficulty=difficulty)
        check = self.generate_check(ctx)

        message = await ctx.send(formatted)
        # using delete_after= kwarg produced desynced results so I
        # decided to manually handle message deletion
        await asyncio.sleep(5)
        await message.delete()
        await ctx.send("What symbols were displayed? Please answer with the "
                       "symbols arranged in the order that they were given.")

        received = await self.bot.wait_for("message", check=check)
        message = self.verify_answer(received.content, answer)
        await ctx.send(message)

    @commands.command()
    async def say(self,
                  ctx,
                  member: Optional[discord.Member], *,
                  message):
        member = member if member else ctx.author
        files = None
        kwargs: dict = None
        webhook = await self._get_webhook(ctx.channel)
        coroutine = webhook.send

        if ctx.message.attachments:
            files = [await a.to_file() for a in ctx.attachments]

        kwargs = {
            "username": member.display_name,
            "avatar_url": member.avatar_url,
            "files": files,
            "allowed_mentions": discord.AllowedMentions(
                everyone=False,
                roles=False
            )
        }

        if member == self.bot.user:
            coroutine = ctx.send
            kwargs.pop("username", None)
            kwargs.pop("avatar_url", None)
        await coroutine(message, **kwargs)


def setup(bot):
    bot.add_cog(Fun(bot))
