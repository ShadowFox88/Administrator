import traceback

import discord
from discord.ext import commands

from base import custom
from converters import Lowered
from objects import Trigger


class Core(custom.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.roles = {
            "community": 761425977401933845,
            "genshin": 763866942074912779,
            "minecraft": 782302123164565556
        }
        self.roles["genshin impact"] = self.roles["genshin"]

        self.bot.loop.create_task(self.__ainit__())

    def get_role(self, name: str):
        _id = self.roles.get(name, -1)

        return self.bot.home.get_role(_id)

    async def __ainit__(self):
        await self.bot.wait_until_ready()
        assigned = 0
        total = 0

        for member in self.bot.home.members:
            if self.community not in member.roles:
                try:
                    await member.add_roles(self.community)
                except discord.Forbidden as e:
                    traceback.print_exception(type(e), e, e.__traceback__)
                else:
                    assigned += 1
                finally:
                    total += 1
        if 0 not in (assigned, total):
            print(f"Assigned community role to {assigned}/{total} members")

    async def _process_trigger(self,
                               member: discord.Member,
                               trigger: Trigger,
                               role: discord.Role):
        if trigger is Trigger.IN:
            if role not in member.roles:
                await member.add_roles(role)
        else:
            if role in member.roles:
                await member.remove_roles(role)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild == self.bot.home:
            await member.add_roles(self.community)

    @commands.command()
    async def opt(self, ctx, trigger: Trigger, *, feature: Lowered):
        feature_found = self.roles.get(feature)
        message = f'No feature called "{feature}"'

        if feature_found:
            message = f"Opted {trigger.name.lower()}: **{feature.title()}**"

            await self._process_trigger(ctx.author, trigger, feature_found)
        await ctx.send(message)


def setup(bot):
    bot.add_cog(Core(bot))
