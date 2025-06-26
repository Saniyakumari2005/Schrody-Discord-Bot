import discord
from discord import app_commands
from discord.ext import commands, tasks
import db
import datetime

from learnlm import ask_learnlm
from sessions import TutoringSession

class Tutor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_inactive_sessions.start()

    @app_commands.command(name="start_session", description="Start a tutoring session.")
    async def start_session(self, interaction: discord.Interaction):
        """Starts a tutoring session and logs the start time."""
        user = interaction.user
        existing_session = db.get_active_session(user.id)

        if existing_session:
            await interaction.response.send_message(f"❌ {user.mention}, you already have an active session with Schrody!", ephemeral=True)
            return
        
        thread = await interaction.channel.create_thread(name=f"Schrody-{user.name}", type=discord.ChannelType.public_thread)
        session = TutoringSession(user, thread)
        self.sessions[thread] = session
        
        db.start_session(interaction.user.id, interaction.user.name)
        await thread.send(f"📚 {user.mention}, Schrody is here to assist you! Ask me anything.")
        await interaction.response.send_message(f"📚 Tutoring session started, {interaction.user.mention}! I'll assist you.")

    @app_commands.command(name="ask", description="Ask Schrody a question.")
    async def ask(self, interaction: discord.Interaction, question: str):
        user_id = str(interaction.user.id)
        
        # Retrieve conversation history
        history = db.get_conversation(user_id)

        # Send to LLM with context
        full_prompt = [{"role": msg["role"], "message": msg["message"]} for msg in history]
        full_prompt.append({"role": "user", "message": question})

        # Save the user's question
        db.add_message(user_id, question, role="user")

        # Get response from LearnLM
        response = ask_learnlm(question)

        # Save AI response
        db.add_message(user_id, response, role="ai")
        
        await interaction.response.send_message(response)


    @app_commands.command(name="end_session", description="End the tutoring session.")
    async def end_session(self, interaction: discord.Interaction):
        """Ends a tutoring session and asks for feedback."""
        db.end_session(interaction.user.id)
        await interaction.response.send_message(f"📌 Your session has ended, {interaction.user.mention}. Please rate your experience with `/feedback <1-5>`.")

    @tasks.loop(minutes=10)
    async def check_inactive_sessions(self):
        """Auto-close inactive sessions after 10 minutes."""
        now = datetime.datetime.utcnow()
        timeout = datetime.timedelta(minutes=10)

        for session in db.sessions_collection.find({"active": True}):
            if now - session["start_time"] > timeout:
                db.end_session(session["user_id"])
                user = await self.bot.fetch_user(int(session["user_id"]))
                await user.send("⏳ Your tutoring session has ended due to inactivity. Please provide feedback with `/feedback <1-5>`.")

async def setup(bot):
    await bot.add_cog(Tutor(bot))
