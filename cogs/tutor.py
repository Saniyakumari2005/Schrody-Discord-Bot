
import discord
from discord import app_commands
from discord.ext import commands, tasks
import db
import datetime
from learnlm import ask_learnlm

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
            await interaction.response.send_message(f"❌ {user.mention}, you already have an active session with Schrödy!", ephemeral=True)
            return

        # Check if we're in an existing Schrödy thread
        if isinstance(interaction.channel, discord.Thread):
            server_name = interaction.guild.name if interaction.guild else "DM"
            expected_thread_name = f"Schrödy-{server_name}"

            if interaction.channel.name == expected_thread_name:
                # We're in an existing Schrody thread - ask for confirmation
                embed = discord.Embed(
                    title="⚠️ New Session Confirmation",
                    description=f"{user.mention}, you're trying to start a new session in an existing thread. This will:",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="What happens if you proceed:",
                    value="• Create a **new conversation** (previous context will be lost)\n• Create a **new thread** in the main channel\n• End any existing session context",
                    inline=False
                )
                embed.add_field(
                    name="Alternatives:",
                    value="• Use `/resume_session` to continue your existing conversation\n• Use `/ask` to continue in this thread if you have an active session",
                    inline=False
                )
                embed.set_footer(text="Use the command again in the main channel if you want to start fresh, or use /resume_session to continue.")

                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        # Use server name instead of username for thread name
        server_name = interaction.guild.name if interaction.guild else "DM"

        # Check if we're in a thread, if so, get the parent channel
        if isinstance(interaction.channel, discord.Thread):
            parent_channel = interaction.channel.parent
            thread = await parent_channel.create_thread(name=f"Schrödy-{server_name}", type=discord.ChannelType.public_thread)
        else:
            thread = await interaction.channel.create_thread(name=f"Schrödy-{server_name}", type=discord.ChannelType.public_thread)
        
        # Store session in the simple format
        self.sessions[user.id] = {
            'thread': thread,
            'user': user,
            'start_time': datetime.datetime.utcnow()
        }

        db.start_session(interaction.user.id, interaction.user.name)
        await thread.send(f"📚 {user.mention}, Schrödy is here to assist you! Ask me anything.")
        await interaction.response.send_message(f"📚 Tutoring session started, {interaction.user.mention}! I'll assist you in the thread I created.")

    @app_commands.command(name="ask", description="Ask Schrody a question.")
    async def ask(self, interaction: discord.Interaction, question: str):
        # Defer the response immediately to prevent timeout
        await interaction.response.defer()

        user_id = str(interaction.user.id)

        # Check if user has an active session
        existing_session = db.sessions_collection.find_one({"user_id": user_id, "active": True})
        if not existing_session:
            embed = discord.Embed(
                title="❌ No Active Session",
                description="You don't have an active tutoring session.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="💡 What you can do:",
                value="1️⃣ **Try resuming:** Use `/resume_session` if you had a previous session\n2️⃣ **Start fresh:** Use `/start_session` to begin a new conversation",
                inline=False
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Check if user has a session and if we're in their thread
        user_session = self.sessions.get(interaction.user.id)
        if not user_session or interaction.channel != user_session['thread']:
            await interaction.followup.send("❌ Please use this command in your tutoring thread or start a new session with `/start_session`.")
            return

        # Show thinking indicator
        thinking_message = await interaction.channel.send("🤔 Schrödy is thinking...")

        # Retrieve conversation history
        history = db.get_conversation(user_id)

        # Build conversation context
        conversation_context = ""
        for msg in history:
            role = "User" if msg["role"] == "user" else "Schrödy"
            conversation_context += f"{role}: {msg['message']}\n"

        # Create contextualized prompt
        if conversation_context:
            contextualized_question = f"Previous conversation:\n{conversation_context}\nUser: {question}"
        else:
            contextualized_question = question

        # Update last activity time and reset reminder flags
        db.sessions_collection.update_one(
            {"user_id": user_id, "active": True},
            {
                "$set": {
                    "last_activity": datetime.datetime.utcnow(),
                    "thread_reminder_sent": False,
                    "dm_warning_sent": False
                }
            }
        )

        # Save the user's question
        db.add_message(user_id, question, role="user")

        # Get response from LearnLM with context
        response = ask_learnlm(contextualized_question)

        # Save AI response
        db.add_message(user_id, response, role="ai")

        # Delete the thinking message
        await thinking_message.delete()

        # Split long messages into chunks to avoid Discord's 2000 character limit
        MAX_LENGTH = 2000
        if len(response) <= MAX_LENGTH:
            await interaction.channel.send(response)
        else:
            # Split the message into chunks
            chunks = []
            current_chunk = ""

            for line in response.split('\n'):
                if len(current_chunk) + len(line) + 1 <= MAX_LENGTH:
                    current_chunk += line + '\n'
                else:
                    if current_chunk:
                        chunks.append(current_chunk.rstrip())
                    current_chunk = line + '\n'

            if current_chunk:
                chunks.append(current_chunk.rstrip())

            # Send each chunk
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await interaction.channel.send(chunk)
                else:
                    await interaction.channel.send(f"**(continued...)**\n{chunk}")

    @app_commands.command(name="resume_session", description="Resume your tutoring session.")
    async def resume_session(self, interaction: discord.Interaction):
        """Resume an existing tutoring session."""
        user = interaction.user
        user_id = str(user.id)

        try:
            # Check if user has an active session in database
            existing_session = db.sessions_collection.find_one({"user_id": user_id, "active": True})
            if not existing_session:
                await interaction.response.send_message(
                    f"❌ {user.mention}, you don't have an active session to resume. Use `/start_session` to begin a new one!", 
                    ephemeral=True
                )
                return

            # Check if session is already in memory
            if user.id in self.sessions:
                session = self.sessions[user.id]
                await interaction.response.send_message(
                    f"✅ {user.mention}, your session is already active! Continue chatting in {session.thread.mention}.", 
                    ephemeral=True
                )
                return

            # Try to find the existing thread
            thread_found = False
            server_name = interaction.guild.name if interaction.guild else "DM"
            thread_name = f"Schrödy-{server_name}"

            # If we're already in the correct thread, just resume here
            if isinstance(interaction.channel, discord.Thread) and interaction.channel.name == thread_name:
                # Check if user is a member of this thread
                if any(member.id == user.id for member in interaction.channel.members):
                    self.sessions[user.id] = {
                        'thread': interaction.channel,
                        'user': user,
                        'start_time': datetime.datetime.utcnow()
                    }

                    # Update last activity time
                    db.sessions_collection.update_one(
                        {"user_id": user_id, "active": True}, 
                        {"$set": {"last_activity": datetime.datetime.utcnow()}}
                    )

                    # Send response first, then the welcome message
                    await interaction.response.send_message(
                        f"✅ {user.mention}, your session has been resumed in this thread!", 
                        ephemeral=True
                    )
                    await interaction.channel.send(f"🔄 {user.mention}, welcome back! Your session has been resumed. Continue asking your questions.")
                    return

            # Search for the thread in the guild
            guild = interaction.guild if interaction.guild else None
            if guild:
                # First check active threads
                active_threads = await guild.active_threads()
                for thread in active_threads:
                    if thread.name == thread_name and any(member.id == user.id for member in thread.members):
                        # Recreate session object
                        self.sessions[user.id] = {
                            'thread': thread,
                            'user': user,
                            'start_time': datetime.datetime.utcnow()
                        }

                        # Update last activity time
                        db.sessions_collection.update_one(
                            {"user_id": user_id, "active": True}, 
                            {"$set": {"last_activity": datetime.datetime.utcnow()}}
                        )

                        await interaction.response.send_message(
                            f"✅ {user.mention}, your session has been resumed in {thread.mention}!", 
                            ephemeral=True
                        )
                        await thread.send(f"🔄 {user.mention}, welcome back! Your session has been resumed. Continue asking your questions.")
                        thread_found = True
                        break

                # If not found in active threads, check archived threads
                if not thread_found:
                    async for thread in guild.archived_threads(limit=50):
                        if thread.name == thread_name and any(member.id == user.id for member in thread.members):
                            # Unarchive the thread by sending a message
                            try:
                                self.sessions[user.id] = {
                                    'thread': thread,
                                    'user': user,
                                    'start_time': datetime.datetime.utcnow()
                                }

                                # Update last activity time
                                db.sessions_collection.update_one(
                                    {"user_id": user_id, "active": True}, 
                                    {"$set": {"last_activity": datetime.datetime.utcnow()}}
                                )

                                await interaction.response.send_message(
                                    f"✅ {user.mention}, your session has been resumed in {thread.mention}!", 
                                    ephemeral=True
                                )
                                await thread.send(f"🔄 {user.mention}, welcome back! Your session has been resumed. Continue asking your questions.")
                                thread_found = True
                                break
                            except discord.Forbidden:
                                # Can't access archived thread
                                continue

            if not thread_found:
                await interaction.response.send_message(
                    f"❌ {user.mention}, couldn't find your previous thread. Use `/start_session` to begin a new session!", 
                    ephemeral=True
                )

        except Exception as e:
            print(f"Error in resume_session: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ {user.mention}, an error occurred while resuming your session. Please try again or start a new session.", 
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"❌ {user.mention}, an error occurred while resuming your session. Please try again or start a new session.", 
                    ephemeral=True
                )

    @app_commands.command(name="end_session", description="End the tutoring session.")
    async def end_session(self, interaction: discord.Interaction):
        """Ends a tutoring session and asks for feedback."""
        session = self.sessions.get(interaction.user.id)
        if session:
            await session['thread'].send(f"✅ {interaction.user.mention}, your tutoring session has ended. Please provide feedback with `/feedback <1-5>`.")
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
        if session and message.channel == session['thread']:
            user_id = str(message.author.id)

            # Check if user has an active session
            existing_session = db.sessions_collection.find_one({"user_id": user_id, "active": True})
            if not existing_session:
                embed = discord.Embed(
                    title="❌ Session Expired",
                    description=f"{message.author.mention}, your tutoring session has expired or ended.",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="💡 What you can do:",
                    value="1️⃣ **Try resuming:** Use `/resume_session` to reconnect to your previous session\n2️⃣ **Start fresh:** Use `/start_session` to begin a new conversation",
                    inline=False
                )
                await message.channel.send(embed=embed)
                return

            # Show thinking indicator
            thinking_message = await message.channel.send("🤔 Schrödy is thinking...")

            # Get conversation history
            history = db.get_conversation(user_id)

            # Build conversation context
            conversation_context = ""
            for msg in history:
                role = "User" if msg["role"] == "user" else "Schrödy"
                conversation_context += f"{role}: {msg['message']}\n"

            # Create contextualized prompt
            if conversation_context:
                contextualized_question = f"Previous conversation:\n{conversation_context}\nUser: {message.content}"
            else:
                contextualized_question = message.content

            # Update last activity time and reset reminder flags
            db.sessions_collection.update_one(
                {"user_id": user_id, "active": True},
                {
                    "$set": {
                        "last_activity": datetime.datetime.utcnow(),
                        "thread_reminder_sent": False,
                        "dm_warning_sent": False
                    }
                }
            )

            # Save the user's question
            db.add_message(user_id, message.content, role="user")

            # Get response from LearnLM with context
            response = ask_learnlm(contextualized_question)

            # Save AI response
            db.add_message(user_id, response, role="ai")

            # Delete the thinking message
            await thinking_message.delete()

            # Split long messages into chunks to avoid Discord's 2000 character limit
            MAX_LENGTH = 2000
            if len(response) <= MAX_LENGTH:
                await message.channel.send(response)
            else:
                # Split the message into chunks
                chunks = []
                current_chunk = ""

                for line in response.split('\n'):
                    if len(current_chunk) + len(line) + 1 <= MAX_LENGTH:
                        current_chunk += line + '\n'
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.rstrip())
                        current_chunk = line + '\n'

                if current_chunk:
                    chunks.append(current_chunk.rstrip())

                # Send each chunk
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        await message.channel.send(chunk)
                    else:
                        await message.channel.send(f"**(continued...)**\n{chunk}")

    @tasks.loop(minutes=5)
    async def check_inactive_sessions(self):
        """Check for inactive sessions and send reminders/close as needed."""
        try:
            now = datetime.datetime.utcnow()

            for session in db.sessions_collection.find({"active": True}):
            time_since_activity = now - session.get("last_activity", session["start_time"])

            # 30 minutes - close session
            if time_since_activity > datetime.timedelta(minutes=30):
                db.end_session(session["user_id"])
                user = await self.bot.fetch_user(int(session["user_id"]))
                await user.send("⏳ Your tutoring session has ended due to inactivity. Please provide feedback with `/feedback <1-5>`.")

                # Clean up session from memory
                if int(session["user_id"]) in self.sessions:
                    del self.sessions[int(session["user_id"])]

            # 15 minutes - send DM warning
            elif time_since_activity > datetime.timedelta(minutes=15) and not session.get("dm_warning_sent", False):
                user = await self.bot.fetch_user(int(session["user_id"]))
                embed = discord.Embed(
                    title="⚠️ Inactivity Warning",
                    description="Your tutoring session will close in 15 minutes due to inactivity.",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="💡 Keep your session active:",
                    value="Send a message in your session thread to continue learning!",
                    inline=False
                )
                await user.send(embed=embed)

                # Mark DM warning as sent
                db.sessions_collection.update_one(
                    {"user_id": session["user_id"], "active": True},
                    {"$set": {"dm_warning_sent": True}}
                )

            # 5 minutes - send thread reminder with interaction
            elif time_since_activity > datetime.timedelta(minutes=5) and not session.get("thread_reminder_sent", False):
                # Find the user's session thread
                user_session = self.sessions.get(int(session["user_id"]))
                if user_session and user_session['thread']:
                    embed = discord.Embed(
                        title="💤 Are you still there?",
                        description=f"<@{session['user_id']}>, you've been inactive for 5 minutes.",
                        color=discord.Color.yellow()
                    )
                    embed.add_field(
                        name="⏰ Session will close in:",
                        value="25 minutes if no activity is detected",
                        inline=False
                    )
                    embed.add_field(
                        name="💬 To continue:",
                        value="Just send any message or question to keep your session active!",
                        inline=False
                    )
                    await user_session['thread'].send(embed=embed)

                    # Mark thread reminder as sent
                    db.sessions_collection.update_one(
                        {"user_id": session["user_id"], "active": True},
                        {"$set": {"thread_reminder_sent": True}}
                    )
        except Exception as e:
            print(f"Error in check_inactive_sessions: {e}")

async def setup(bot):
    await bot.add_cog(Tutor(bot))
