import datetime
import io
import operator
import os
import random
import re
from typing import List
from typing import Optional
from typing import Tuple

import discord
from discord.ext import commands
from discord.ext import flags
from discord.ext import tasks

from base import custom
from converters import OperationConverter
from errors import WorksheetsError
from objects import Operation
from objects import CST


def positive_int(arg: str):
    arg = int(arg)

    if arg > 0:
        return arg
    raise commands.BadArgument("integer must be positive")


class Worksheets(custom.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.message: str = None
        self.question_format = re.compile(
            r"(?P<x>\d{1,2})\s*"
            r"(?P<operator>[\+-x÷])\s*"
            r"(?P<y>\d{1,2})\s*=\s*"
            r"(?P<answer>\d{1,3}?)"
            r"(?P<has_carriage_return>\r)?"
        )
        self.CST = CST()

        self.bot.loop.create_task(self.__ainit__())

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
        now = datetime.datetime.now(tz=self.CST)
        target = datetime.datetime(now.year,
                                   now.month,
                                   now.day,
                                   hour=12,
                                   tzinfo=self.CST)

        if now < target:
            return target
        return target + datetime.timedelta(days=1)

    def _bulk_write(self,
                    message: str,
                    streams: Tuple[io.BytesIO],
                    **kwargs):
        for i, stream in enumerate(streams):
            print(stream, type(stream))
            format_kwargs = {k: v[i] for k, v in kwargs.items()}
            content = message.format(**format_kwargs).encode("UTF-8")

            stream.write(content)

    def create_worksheet(self, operation: Operation):
        now = datetime.datetime.now()
        filename = now.strftime("%d-%m-%Y.txt")
        streams = (io.BytesIO(), io.BytesIO())

        for _ in range(flags["questions"]):
            x = random.randint(1, 12)
            y = random.randint(1, 12)
            answer = operation(x, y)
            message = f"{x} {operation.symbol} {y} = {{answer}}\n"

            self._bulk_write(message, streams, answer=[answer, ""])
        self._bulk_write("\nTime: \n", streams)

        with open(f"internal/{filename}", "wb") as f:
            stream = streams[0]
            f.write(stream.read())
        return discord.File(streams[1], filename)

    def validate_worksheets(self,
                            operation: Optional[Operation],
                            attachments: List[discord.Attachment]):
        stream = io.BytesIO()
        success = 0
        total = 0
        has_carriage_return: bool = None
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

                if has_carriage_return is None:
                    has_carriage_return = bool(
                        question_found.group("has_carriage_return")
                    )

                if operation is None:
                    operation = question_found.group("operator")
                args = ("x", "y", "answer")
                x, y, response = map(int, question_found.group(*args))
                answer = operation(x, y)

                if response == answer:
                    success += 1
                else:
                    append += f" ❌ {answer}"

                if has_carriage_return:
                    append += "\r"
                append += "\n"
                stream.write(append)
        append = f"Results: {success}/{total}"
        line_ending = "\n"

        if has_carriage_return:
            line_ending = "\r\n"
        stream.write(f"{line_ending}Results: {success}/{total}{line_ending}")
        return discord.File(stream, filename)

    @tasks.loop()
    async def _remind(self, operation: Operation):
        target = self._get_next_target_date()
        await discord.utils.sleep_until(target)

        file = self.create_worksheet(operation)
        await self.bot_channel.send(self.message, file=file)

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
            file = self.create_worksheet(operation)
        else:
            if not ctx.message.attachments:
                raise WorksheetsError("no attachment found")
            file = self.validate_worksheets(operation, ctx.message.attachments)
        await ctx.send(content, file=file)


def setup(bot):
    bot.add_cog(Worksheets(bot))
