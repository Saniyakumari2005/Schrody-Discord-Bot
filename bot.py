import discord
from discord.ext import commands
from discord import Bot, app_commands
import logging
import db
import config


#Enable logging
logging.basicConfig(level=logging.INFO)

#Bot intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

#Initialize bot with a slash command
class Schrody(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=None, intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        """Sync commands when bot starts."""
        await self.load_extension("cogs.tutor")
        await self.load_extension("cogs.feedback")
        await self.tree.sync()
        print(f"✅ Synced {len(self.tree.get_commands())} slash commands.")

bot = Schrody()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.tree.command(name="Hello", description="Sends a greeting")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello, {interaction.user.mention}! How can I help?")

if not config.TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is not set")
bot.run(config.TOKEN)