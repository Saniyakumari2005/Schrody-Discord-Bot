import discord
from discord import app_commands
from discord.ext import commands, tasks
import db
import datetime

class Feedback(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.remind_feedback.start()

    @app_commands.command(name="feedback", description="Submit feedback (1-5).")
    async def feedback(self, interaction: discord.Interaction, rating: int):
        """Logs user feedback."""
        if rating < 1 or rating > 5:
            await interaction.response.send_message("❌ Please provide a rating between 1 and 5.")
            return

        db.log_feedback(interaction.user.id, rating)
        await interaction.response.send_message("✅ Thanks for your feedback!")

    @app_commands.command(name="pending_feedback", description="List users who haven't given feedback.")
    async def pending_feedback(self, interaction: discord.Interaction):
        """Lists users who haven't submitted feedback."""
        pending_users = db.get_pending_feedback()
        if len(list(pending_users)) == 0:
            await interaction.response.send_message("✅ Everyone has submitted feedback!")
            return
        
        user_list = "\n".join([user["username"] for user in pending_users])
        await interaction.response.send_message(f"🚨 Users who haven't submitted feedback:\n```{user_list}```")

    @tasks.loop(hours=12)
    async def remind_feedback(self):
        """Reminds users to submit feedback every 12 hours."""
        for session in db.get_pending_feedback():
            user = await self.bot.fetch_user(int(session["user_id"]))
            await user.send("🔔 Reminder: Schrody is waiting for your feedback! Please use `/feedback <1-5>`.")

async def setup(bot):
    await bot.add_cog(Feedback(bot))
