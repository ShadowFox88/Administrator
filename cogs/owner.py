from discord.ext import commands

from base import custom


class Owner(custom.Cog, hidden=True):
    def __init__(self, bot):
        self.bot = bot

        self._original_get_context = self.bot.get_context
        self.bot.get_context = self.get_context

    def cog_unload(self):
        self.bot.get_context = self._original_get_context

    async def _attempt_fetch(self, payload):
        channel_found = self.bot.get_channel(payload.channel_id)

        if not channel_found:
            return None
        return await channel_found.fetch_message(payload.message_id)

    async def get_context(self, message, *, cls=custom.Context):
        return await self._original_get_context(message, cls=cls)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        message_found = await self._attempt_fetch(payload)

        if message_found:
            await self.bot.process_commands(message_found)


def setup(bot):
    bot.add_cog(Owner(bot))
