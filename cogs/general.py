
import discord
from discord import app_commands
from discord.ext import commands

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check if the bot is responsive.")
    async def ping(self, interaction: discord.Interaction):
        """Simple ping command to test bot responsiveness."""
        await interaction.response.send_message(f"🏓 Pong! Latency: {round(self.bot.latency * 1000)}ms")

async def setup(bot):
    await bot.add_cog(General(bot))
