import datetime
import learnlm
import db
import discord

class TutoringSession:
    """Represents an individual tutoring session for a user."""

    def __init__(self, user, thread):
        self.user = user
        self.thread = thread
        self.start_time = datetime.datetime.utcnow()
        self.active = True

    async def process_message(self, message):
        """Processes user input and gets a response from LearnLM."""
        if not self.active:
            return await message.channel.send("❌ This session has ended. Start a new one with `/start_session`.")

        response = learnlm.ask_learnlm(message.content)
        await message.channel.send(response)

    async def end_session(self):
        """Ends the tutoring session."""
        self.active = False
        db.end_session(self.user.id)
        await self.thread.send(f"✅ {self.user.mention}, your tutoring session has ended. Please provide feedback with `/feedback <1-5>`.")
