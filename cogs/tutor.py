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
        self.sessions = {}
        self.check_inactive_sessions.start()

    @app_commands.command(name="start_session", description="Start a tutoring session.")
    async def start_session(self, interaction: discord.Interaction):
        """Starts a tutoring session and logs the start time."""
        user = interaction.user
        existing_session = db.sessions_collection.find_one({"user_id": str(user.id), "active": True})

        if existing_session:
            await interaction.response.send_message(f"❌ {user.mention}, you already have an active session with Schrody!", ephemeral=True)
            return

        # Use server name instead of username for thread name
        server_name = interaction.guild.name if interaction.guild else "DM"
        thread = await interaction.channel.create_thread(name=f"Schrody-{server_name}", type=discord.ChannelType.public_thread)
        session = TutoringSession(user, thread)
        self.sessions[user.id] = session

        db.start_session(interaction.user.id, interaction.user.name)
        await thread.send(f"📚 {user.mention}, Schrody is here to assist you! Ask me anything.")
        await interaction.response.send_message(f"📚 Tutoring session started, {interaction.user.mention}! I'll assist you in the thread I created.")

    @app_commands.command(name="ask", description="Ask Schrody a question.")
    async def ask(self, interaction: discord.Interaction, question: str):
        # Defer the response immediately to prevent timeout
        await interaction.response.defer()

        user_id = str(interaction.user.id)

        # Check if user has an active session
        existing_session = db.sessions_collection.find_one({"user_id": user_id, "active": True})
        if not existing_session:
            await interaction.followup.send("❌ You don't have an active session. Start one with `/start_session` first!")
            return

        # Get the user's session
        session = self.sessions.get(interaction.user.id)
        if not session:
            await interaction.followup.send("❌ Session not found. Please start a new session with `/start_session`.")
            return

        # Retrieve conversation history
        history = db.get_conversation(user_id)

        # Build conversation context
        conversation_context = ""
        for msg in history:
            role = "User" if msg["role"] == "user" else "Schrody"
            conversation_context += f"{role}: {msg['message']}\n"

        # Create contextualized prompt
        if conversation_context:
            contextualized_question = f"Previous conversation:\n{conversation_context}\nUser: {question}"
        else:
            contextualized_question = question

        # Save the user's question
        db.add_message(user_id, question, role="user")

        # Get response from LearnLM with context
        response = ask_learnlm(contextualized_question)

        # Save AI response
        db.add_message(user_id, response, role="ai")

        # Truncate response if it exceeds Discord's 2000 character limit
        MAX_LENGTH = 2000
        if len(response) > MAX_LENGTH:
            truncated_response = response[:MAX_LENGTH-50] + "\n\n...(response truncated)"
        else:
            truncated_response = response

        # Send response to the thread
        await session.thread.send(truncated_response)

    @app_commands.command(name="end_session", description="End the tutoring session.")
    async def end_session(self, interaction: discord.Interaction):
        """Ends a tutoring session and asks for feedback."""
        session = self.sessions.get(interaction.user.id)
        if session:
            await session.thread.send(f"✅ {interaction.user.mention}, your tutoring session has ended. Please provide feedback with `/feedback <1-5>`.")
            del self.sessions[interaction.user.id]

        db.end_session(interaction.user.id)
        await interaction.response.send_message(f"📌 Your session has ended, {interaction.user.mention}. Please rate your experience with `/feedback <1-5>`.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages in tutoring threads and respond automatically."""
        # Ignore bot messages
        if message.author.bot:
            return

        # Check if message is in a tutoring thread
        session = self.sessions.get(message.author.id)
        if session and message.channel == session.thread:
            user_id = str(message.author.id)

            # Check if user has an active session
            existing_session = db.sessions_collection.find_one({"user_id": user_id, "active": True})
            if not existing_session:
                await message.channel.send("❌ Your session has expired. Start a new one with `/start_session`!")
                return

            # Get conversation history
            history = db.get_conversation(user_id)

            # Build conversation context
            conversation_context = ""
            for msg in history:
                role = "User" if msg["role"] == "user" else "Schrody"
                conversation_context += f"{role}: {msg['message']}\n"

            # Create contextualized prompt
            if conversation_context:
                contextualized_question = f"Previous conversation:\n{conversation_context}\nUser: {message.content}"
            else:
                contextualized_question = message.content

            # Save the user's question
            db.add_message(user_id, message.content, role="user")

            # Get response from LearnLM with context
            response = ask_learnlm(contextualized_question)

            # Save AI response
            db.add_message(user_id, response, role="ai")

            # Truncate response if it exceeds Discord's 2000 character limit
            MAX_LENGTH = 2000
            if len(response) > MAX_LENGTH:
                truncated_response = response[:MAX_LENGTH-50] + "\n\n...(response truncated)"
            else:
                truncated_response = response

            # Send response to the thread
            await message.channel.send(truncated_response)

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