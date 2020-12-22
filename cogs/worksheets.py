import datetime
import io
import operator
import random
import re

import discord
from discord.ext import commands
from discord.ext import flags
from discord.ext import tasks

from base import custom
from converters import OperationConverter
from errors import WorksheetsError
from objects import Operation

date = re.compile(
    r"^(?P<day>\d{1,2})-(?P<month>\d{1,2})-(?P<year>\d{4})$"
)


def date_format(arg: str):
    date_found = date.fullmatch(arg)

    if date_found:
        day, month = (s.zfill(2) for s in date_found.group("day", "month"))
        year = date_found.group("year")

        return f"{day}-{month}-{year}"
    raise commands.BadArgument("invalid date format passed")


def positive_int(arg: str):
    arg = int(arg)

    if arg > 0:
        return arg
    raise commands.BadArgument("integer must be positive")


class CST(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(hours=-6)

    def dst(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return "-06:00"


class Worksheets(custom.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.message: str = None
        self.question_format = re.compile(
            r"(\d{1,2}\s*[\+-x÷]\s*\d{1,2}\s*=\s*\d{1,3}?\r?\n)"
        )
        self.time_format = re.compile(
            r"^Time:\s*(?P<minutes>\d{1,2}):\s*(?P<seconds>\d{2})$"
        )
        self.CST = CST()

        operation = OperationConverter.OPERATORS["mul"]
        self._remind.start(operation)

    async def __ainit__(self):
        await self.bot.wait_until_ready()
        self.message = f"{self.kai.mention} Study"

    @property
    def bot_channel(self):
        return self.bot.home.get_channel(531807782916194314)

    @property
    def kai(self):
        return self.bot.home.get_member(297874688145752066)

    def _get_next_target_date_from(self, now: datetime.datetime):
        now = datetime.datetime.now(tz=self.CST)
        target = datetime.datetime(now.year,
                                   now.month,
                                   now.day,
                                   hour=12,
                                   tzinfo=self.CST)

        if now < target:
            return target
        return target + datetime.timedelta(days=1)

    def gen_question(self, operation):
        y = None
        args = [1, 12]
        x = random.randint(1, 12)
        function = random.randint

        if operation == operator.sub:
            args[1] = x
        elif operation == operator.floordiv:
            function = random.choice
            x = random.randint(1, 10)
            multiplier = random.randint(1, 10)
            args = [x, multiplier]
            x *= multiplier

        if len(args) == 1:
            y = args[0]
        else:
            try:
                y = function(*args)
            except TypeError:
                y = function(args)
        return x, y

    def create_worksheet(self, operation: Operation, date: str, q_num: int):
        stream = io.BytesIO()

        for i in range(1, q_num + 1):
            x, y = self.gen_question(operation)
            encoded = (f"{x} {operation.symbol} {y} = \n").encode("UTF-8")
            stream.write(encoded)
        stream.write(("\nTime: \n").encode("UTF-8"))
        stream.seek(0)
        return stream

    def validate_worksheet(self, date: str):
        time = None
        total = 0
        correct = 0

        with open(f"{date}.txt", "r") as q_file:
            with open(f"{date}-ANSWERS.txt", "r") as a_file:
                questions = q_file.readlines()
                answers = a_file.readlines()

                for question, answer in zip(questions, answers):
                    # save processing power for expensive functions
                    # e.g. regex
                    if question.strip() == "":
                        continue
                    result = self.question_format.search(question)

                    if result is not None:
                        total += 1

                        if result.group() == answer:
                            correct += 1
                    else:
                        time_found = self.time_format.match(question)

                        if time_found is not None:
                            minutes, seconds = time_found.groups()
                            time = f"{minutes}m {seconds}s"
        return correct, total, time

    @tasks.loop()
    async def _remind(self, operation: Operation):
        now = datetime.datetime.now(tz=self.CST)
        target = self._get_next_target_date_from(now)

        if now < target:
            await discord.utils.sleep_until(target)
        date = datetime.datetime.now().strftime("%d-%m-%Y")
        stream = self.create_worksheet(operation, date, 30)
        file = discord.File(stream, filename=f"{date}.txt")
        await self.bot_channel.send(self.message, file=file)

    @_remind.before_loop
    async def _before_remind(self):
        await self.bot.wait_until_ready()
        print("Running task:", f"{self.__class__.__name__}._remind")

    @flags.add_flag("--questions", type=positive_int, default=30)
    @flags.add_flag("--validate", action="store_true")
    @flags.add_flag("--date",
                    type=date_format,
                    default=datetime.datetime.now().strftime("%d-%m-%Y"))
    @flags.command()
    async def worksheets(self, ctx, operation: OperationConverter, **flags):
        function = self.create_worksheet
        args = (operation, flags["date"], flags["questions"])

        if flags["validate"]:
            function = self.validate_worksheet

            if ctx.attachments:
                pass
            raise WorksheetsError("No file attached")
        data = function(*args)

        if isinstance(data, tuple):
            correct, total, time = data
        else:
            filename = flags["date"] + ".txt"
            file = discord.File(data, filename=filename)

            await ctx.send(file=file)


def setup(bot):
    bot.add_cog(Worksheets(bot))
