import datetime
import learnlm
import db
import discord
from typing import Dict, Optional

class UserSession:
    """Represents an individual user's session within a tutoring thread."""
    
    def __init__(self, user, thread):
        self.user = user
        self.thread = thread
        self.start_time = datetime.datetime.utcnow()
        self.active = True
        self.conversation_history = []  # Store user-specific conversation history
        self.last_activity = datetime.datetime.utcnow()
    
    def add_to_history(self, message_content: str, response: str):
        """Add message and response to user's conversation history."""
        self.conversation_history.append({
            'timestamp': datetime.datetime.utcnow(),
            'user_message': message_content,
            'bot_response': response
        })
        self.last_activity = datetime.datetime.utcnow()
    
    def get_context(self) -> str:
        """Get conversation context for this specific user."""
        if not self.conversation_history:
            return ""
        
        # Return last few exchanges for context (adjust number as needed)
        recent_history = self.conversation_history[-5:]  # Last 5 exchanges
        context = []
        for entry in recent_history:
            context.append(f"User: {entry['user_message']}")
            context.append(f"Assistant: {entry['bot_response']}")
        
        return "\n".join(context)

class TutoringSession:
    """Represents a tutoring session that can handle multiple users in the same thread."""

    def __init__(self, thread):
        self.thread = thread
        self.start_time = datetime.datetime.utcnow()
        self.active = True
        self.user_sessions: Dict[int, UserSession] = {}  # user_id -> UserSession
        self.session_timeout = 3600  # 1 hour timeout for inactive users
    
    def add_user(self, user) -> UserSession:
        """Add a new user to the session or return existing user session."""
        if user.id not in self.user_sessions:
            self.user_sessions[user.id] = UserSession(user, self.thread)
        return self.user_sessions[user.id]
    
    def get_user_session(self, user_id: int) -> Optional[UserSession]:
        """Get user session by user ID."""
        return self.user_sessions.get(user_id)
    
    def remove_inactive_users(self):
        """Remove users who have been inactive for too long."""
        try:
            current_time = datetime.datetime.utcnow()
            inactive_users = []
            
            for user_id, user_session in self.user_sessions.items():
                try:
                    # Check if last_activity exists and is valid
                    if hasattr(user_session, 'last_activity') and user_session.last_activity:
                        time_since_activity = (current_time - user_session.last_activity).total_seconds()
                        if time_since_activity > self.session_timeout:
                            inactive_users.append(user_id)
                    else:
                        # If last_activity is missing, consider user inactive
                        inactive_users.append(user_id)
                except (AttributeError, TypeError, ValueError) as e:
                    # If there's any error calculating time, mark user as inactive
                    print(f"Error calculating activity time for user {user_id}: {e}")
                    inactive_users.append(user_id)
            
            # Remove inactive users
            for user_id in inactive_users:
                if user_id in self.user_sessions:
                    del self.user_sessions[user_id]
                    
        except Exception as e:
            print(f"Error in remove_inactive_users: {e}")
            # Continue execution even if cleanup fails
    
    async def process_message(self, message):
        """Processes user input and gets a response from LearnLM with user-specific context."""
        if not self.active:
            return await message.channel.send("❌ This session has ended. Start a new one with `/start_session`.")
        
        # Clean up inactive users periodically
        self.remove_inactive_users()
        
        # Get or create user session
        user_session = self.add_user(message.author)
        
        if not user_session.active:
            return await message.channel.send(f"❌ {message.author.mention}, your individual session has ended. Rejoin with `/join_session`.")
        
        # Get user-specific context
        context = user_session.get_context()
        
        # Prepare message with context for LearnLM
        contextual_message = f"User: {message.author.display_name}\n"
        if context:
            contextual_message += f"Previous conversation:\n{context}\n\n"
        contextual_message += f"Current message: {message.content}"
        
        # Get response from LearnLM
        response = learnlm.ask_learnlm(contextual_message)
        
        # Add to user's conversation history
        user_session.add_to_history(message.content, response)
        
        # Send response mentioning the user
        await message.channel.send(f"{message.author.mention}, {response}")
    
    async def end_user_session(self, user):
        """Ends a specific user's session."""
        if user.id in self.user_sessions:
            user_session = self.user_sessions[user.id]
            user_session.active = False
            db.end_session(user.id, self.thread.id)
            
            # Remove user from active sessions
            del self.user_sessions[user.id]
        else:
            await self.thread.send(f"❌ {user.mention}, you don't have an active session.")
    
    async def end_session(self):
        """Ends the entire tutoring session for all users."""
        self.active = False
        
        # End all user sessions
        for user_id, user_session in self.user_sessions.items():
            user_session.active = False
            db.end_session(user_id, self.thread.id)
        
        # Notify all users
        user_mentions = [f"<@{user_id}>" for user_id in self.user_sessions.keys()]
        if user_mentions:
            mentions_text = ", ".join(user_mentions)
            await self.thread.send(f"✅ {mentions_text}, the tutoring session has ended. Please provide feedback with `/feedback <1-5>`.")
        
        self.user_sessions.clear()
    
    def get_active_users(self) -> list:
        """Get list of active users in the session."""
        return [user_session.user for user_session in self.user_sessions.values() if user_session.active]
    
    def get_session_stats(self) -> dict:
        """Get statistics about the session."""
        return {
            'total_users': len(self.user_sessions),
            'active_users': len([us for us in self.user_sessions.values() if us.active]),
            'session_duration': (datetime.datetime.utcnow() - self.start_time).total_seconds(),
            'users': [us.user.display_name for us in self.user_sessions.values()]
        }

# Example usage in your bot commands:

# You'll also need to modify your session management:
class SessionManager:
    """Manages multiple tutoring sessions across different threads."""
    
    def __init__(self):
        self.sessions: Dict[int, TutoringSession] = {}  # thread_id -> TutoringSession
    
    def create_session(self, thread) -> TutoringSession:
        """Create a new tutoring session for a thread."""
        session = TutoringSession(thread)
        self.sessions[thread.id] = session
        return session
    
    def get_session(self, thread_id: int) -> Optional[TutoringSession]:
        """Get existing session by thread ID."""
        return self.sessions.get(thread_id)
    
    def end_session(self, thread_id: int):
        """End and remove a session."""
        if thread_id in self.sessions:
            del self.sessions[thread_id]
    
    def cleanup_inactive_sessions(self):
        """Clean up inactive users across all sessions."""
        try:
            for session in self.sessions.values():
                if session.active:
                    session.remove_inactive_users()
        except Exception as e:
            print(f"Error in cleanup_inactive_sessions: {e}")
    
    def get_all_sessions_stats(self) -> dict:
        """Get statistics for all active sessions."""
        return {
            'total_sessions': len(self.sessions),
            'active_sessions': len([s for s in self.sessions.values() if s.active]),
            'total_users': sum(len(s.user_sessions) for s in self.sessions.values())
        }

# Global session manager instance
session_manager = SessionManager()

# Example bot command handlers:
async def start_session_command(slash):
    """Start a new tutoring session in the current thread."""
    session = session_manager.create_session(slash.channel)
    await slash.send(f"🎓 Tutoring session started! Users can now ask questions and I'll maintain separate conversations with each person.")

async def join_session_command(slash):
    """Join an existing tutoring session."""
    session = session_manager.get_session(slash.channel.id)
    if session and session.active:
        user_session = session.add_user(slash.author)
        await slash.send(f"✅ {slash.author.mention}, you've joined the tutoring session!")
    else:
        await slash.send("❌ No active tutoring session in this thread. Start one with `/start_session`.")

async def leave_session_command(slash):
    """Leave the current tutoring session."""
    session = session_manager.get_session(slash.channel.id)
    if session:
        await session.end_user_session(slash.author)
    else:
        await slash.send("❌ No active tutoring session in this thread.")

async def session_stats_command(slash):
    """Show statistics about the current session."""
    session = session_manager.get_session(slash.channel.id)
    if session and session.active:
        stats = session.get_session_stats()
        await slash.send(f"📊 Session Stats:\n"
                        f"• Total users: {stats['total_users']}\n"
                        f"• Active users: {stats['active_users']}\n"
                        f"• Duration: {stats['session_duration']:.0f} seconds\n"
                        f"• Users: {', '.join(stats['users'])}")
    else:
        await slash.send("❌ No active tutoring session in this thread.")