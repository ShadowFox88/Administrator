import datetime
import io
import os
import random
import re
from typing import List, Optional

import discord
from discord.ext import commands, flags, tasks

from base import custom
from converters import OperationConverter
from errors import WorksheetsError
from objects import Operation, MST


def positive_int(arg: str):
    arg = int(arg)

    if arg > 0:
        return arg
    raise commands.BadArgument("integer must be positive")


class Worksheets(custom.Cog):
    def __init__(self, bot):
        self.bot = bot

        operation = OperationConverter.OPERATORS["mul"]
        self.message: str = None
        self.question_format = re.compile(
            r"(?P<x>[0-9]{1,2})\s*"
            r"(?P<operator>[\+-x÷])\s*"
            r"(?P<y>[0-9]{1,2})\s*=\s*"
            r"(?P<answer>[0-9]{1,3})?"
        )
        self.MST = MST()

        self.bot.loop.create_task(self.__ainit__())
        self._remind.start(operation, questions=30)

    def cog_unload(self):
        self._remind.cancel()

    async def __ainit__(self):
        await self.bot.wait_until_ready()
        self.message = f"{self.kai.mention} Study"

    @property
    def bot_channel(self):
        return self.bot.home.get_channel(531807782916194314)

    @property
    def kai(self):
        return self.bot.home.get_member(297874688145752066)

    def _get_next_target_date(self):
        now = datetime.datetime.now(tz=self.MST)
        target = datetime.datetime(now.year,
                                   now.month,
                                   now.day,
                                   hour=12,
                                   tzinfo=self.MST)

        if now < target:
            return target
        return target + datetime.timedelta(days=1)

    def create_worksheet(self, operation: Operation, questions: int = 30):
        now = datetime.datetime.now()
        filename = now.strftime("%d-%m-%Y.txt")
        stream = io.BytesIO()

        for _ in range(questions):
            x = random.randint(1, 12)
            y = random.randint(1, 12)
            answer = operation(x, y)

            stream.write(str.encode(f"{x} {operation.symbol} {y} = {answer}\n"))
        stream.write(str.encode("\nTime: \n"))
        stream.seek(0)
        return discord.File(stream, filename)

    async def validate_worksheets(self,
                                  operation: Optional[Operation],
                                  attachments: List[discord.Attachment]):
        stream = io.BytesIO()
        success = 0
        total = 0
        attachment = attachments[0]
        name, _ = os.path.splitext(attachment.filename)
        filename = f"{name}-ANSWERS.txt"
        content = await attachment.read()

        if content[:3] == b"\xef\xbb\xbf":
            content = content[3:]
        content = content.decode()

        for line in content.split("\n"):
            question_found = self.question_format.match(line)

            if question_found:
                append = line.strip()
                total += 1

                # UNTESTED
                if operation is None:
                    operation = discord.utils.get(
                        OperationConverter.OPERATORS.values(),
                        symbol=question_found.group("operator")
                    )
                # UNTESTED
                args = ("x", "y", "answer")
                x, y, response = map(int, question_found.group(*args))
                answer = operation(x, y)

                if response == answer:
                    success += 1
                else:
                    append += f" ❌ {answer}"
                stream.write(str.encode(f"{append}\n"))
        stream.write(str.encode(f"\nResults: {success}/{total}\n"))
        stream.seek(0)
        return discord.File(stream, filename)

    @tasks.loop()
    async def _remind(self, operation: Operation, questions: int):
        date = self._get_next_target_date()
        await discord.utils.sleep_until(date)

        file = self.create_worksheet(operation, questions)
        await self.bot_channel.send(self.message, file=file)

    @_remind.before_loop
    async def _before_remind(self):
        await self.bot.wait_for_display()
        print("Running _remind.start()")

    @flags.add_flag("--questions", type=positive_int, default=30)
    @flags.add_flag("--validate", action="store_true")
    @flags.command()
    async def worksheets(self,
                         ctx,
                         operation: Optional[OperationConverter],
                         **flags):
        content: Optional[str] = self.message

        if flags["validate"]:
            content = None

            if not ctx.message.attachments:
                raise WorksheetsError("no attachment found")
            file = await self.validate_worksheets(operation,
                                                  ctx.message.attachments)
        else:
            file = self.create_worksheet(operation, flags["questions"])
        await ctx.send(content, file=file)


def setup(bot):
    bot.add_cog(Worksheets(bot))
