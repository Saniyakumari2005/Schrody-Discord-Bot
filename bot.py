import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
import signal
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging for Railway (console output)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Only console for Railway(might delete later)
    ]
)
logger = logging.getLogger(__name__)

# Bot intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

# Initialize bot with a slash command
class Schrody(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        """Sync commands when bot starts."""
        try:
            await self.load_extension("cogs.tutor")
            logger.info("✅ Loaded tutor cog")
        except Exception as e:
            logger.error(f"❌ Failed to load tutor cog: {e}")
        
        try:
            await self.load_extension("cogs.feedback")
            logger.info("✅ Loaded feedback cog")
        except Exception as e:
            logger.error(f"❌ Failed to load feedback cog: {e}")
        
        try:
            await self.load_extension("cogs.database")
            logger.info("✅ Loaded database cog")
        except Exception as e:
            logger.error(f"❌ Failed to load database cog: {e}")
        
        try:
            await self.load_extension("cogs.general")
            logger.info("✅ Loaded general cog")
        except Exception as e:
            logger.error(f"❌ Failed to load general cog: {e}")
        
        try:
            await self.tree.sync()
            logger.info(f"✅ Synced {len(self.tree.get_commands())} slash commands.")
        except Exception as e:
            logger.error(f"❌ Failed to sync commands: {e}")

bot = Schrody()

# Global error handler
@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f'An error occurred in {event}: {args}', exc_info=True)

# Command error handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Use `!help` to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param}")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    else:
        logger.error(f'Command error in {ctx.command}: {error}', exc_info=True)
        await ctx.send("An error occurred while processing the command.")

# Bot ready event
@bot.event
async def on_ready():
    logger.info(f"✅ Logged in as {bot.user}")
    logger.info(f'Bot is in {len(bot.guilds)} guilds')
    
    # Set bot status (optional)
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="for commands")
    )


@bot.tree.command(name="hello", description="Sends a greeting")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello, {interaction.user.mention}! How can I help?")

async def load_cogs():
    """Load all cogs from the cogs directory"""
    pass

# Graceful shutdown handler
def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    asyncio.create_task(shutdown())

async def shutdown():
    """Gracefully shutdown the bot"""
    logger.info("Shutting down bot...")
    await bot.close()
    logger.info("Bot shut down complete")

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Main function to run the bot
async def main():
    """Main function to start the bot"""
    try:
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            logger.error("DISCORD_TOKEN not found in environment variables")
            sys.exit(1)
        
        # Start the bot
        logger.info("Starting bot...")
        await bot.start(token)
        
    except discord.LoginFailure:
        logger.error("Invalid Discord token provided")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        sys.exit(1)

# Run the bot
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)