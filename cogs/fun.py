import asyncio
import random
import re

from discord.ext import commands

from base import custom
from converters import DifficultyConverter


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
    async def memory(self, ctx, difficulty: DifficultyConverter = 6):
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


def setup(bot):
    bot.add_cog(Fun(bot))
