import os
import pymongo
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
mongo_client = MongoClient(os.getenv("MONGO_URI"))
db = mongo_client[os.getenv("MONGO_DB")]
conversations = db.conversations

# Collections
users_collection = db["users"]
messages_collection = db["messages"]
sessions_collection = db["sessions"]
feedback_collection = db["feedback"]

def add_user(discord_id, username):
    """Add a user to the database if they don't exist."""
    user = users_collection.find_one({"discord_id": str(discord_id)})
    if not user:
        users_collection.insert_one({"discord_id": str(discord_id), "username": username})
        print(f"✅ User {username} added to database.")

def log_message(user_id, message):
    """Log user messages for future tutoring assistance."""
    messages_collection.insert_one({
        "user_id": str(user_id),
        "message": message
    })
    print(f"💾 Logged message from user {user_id}")

def get_messages(user_id, limit=10):
    """Retrieve the last N messages from a user."""
    return list(messages_collection.find({"user_id": str(user_id)}).sort("_id", -1).limit(limit))

def start_session(user_id, username):
    """Start a tutoring session."""
    session = {
        "user_id": str(user_id),
        "username": username,
        "start_time": datetime.datetime.utcnow(),
        "active": True,
        "feedback_given": False
    }
    sessions_collection.insert_one(session)

def end_session(user_id):
    """End a tutoring session."""
    sessions_collection.update_one({"user_id": str(user_id), "active": True}, {"$set": {"active": False}})

def log_feedback(user_id, rating):
    """Store feedback rating."""
    feedback_collection.insert_one({
        "user_id": str(user_id),
        "rating": rating,
        "timestamp": datetime.datetime.utcnow()
    })
    sessions_collection.update_one({"user_id": str(user_id)}, {"$set": {"feedback_given": True}})

def get_pending_feedback():
    """Get list of users who haven't submitted feedback."""
    return sessions_collection.find({"active": False, "feedback_given": False})

def add_message(user_id, message, role="user"):
    """Save a user or AI message to the conversation memory."""
    conversations.insert_one({
        "user_id": user_id,
        "message": message,
        "role": role
    })

def get_conversation(user_id, limit=10):
    """Retrieve recent messages for context."""
    msgs = list(conversations.find({"user_id": user_id}).sort("_id", -1).limit(limit))
    return [{"role": msg["role"], "message": msg["message"]} for msg in reversed(msgs)]

def clear_conversation(user_id):
    """Clear the conversation memory."""
    conversations.delete_many({"user_id": user_id})