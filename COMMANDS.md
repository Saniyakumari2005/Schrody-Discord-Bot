
# Schrody Discord Bot - Slash Commands Reference

## 🤖 **Bot Overview**
Schrody is an AI-powered tutoring Discord bot that uses the Gemini API for educational assistance and MongoDB for data storage.

---

## 📋 **All Slash Commands**

### **🎯 Core Bot Commands**
| Command | Description |
|---------|-------------|
| `/hello` | Sends a greeting message to the user |
| `/ping` | Check if the bot is responsive and show latency |

### **📚 Tutoring Commands**
| Command | Description | Requirements |
|---------|-------------|--------------|
| `/start_session` | Start a tutoring session with Schrody | None |
| `/ask <question>` | Ask Schrody a question | Active session required |
| `/resume_session` | Resume an existing tutoring session | Previous active session |
| `/end_session` | End the current tutoring session | Active session |

### **💬 Feedback Commands**
| Command | Description | Parameters |
|---------|-------------|------------|
| `/feedback <rating>` | Submit feedback with a rating | Rating: 1-5 |
| `/pending_feedback` | List users who haven't given feedback yet | Admin only |

### **🗄️ Database Management Commands**
| Command | Description | Purpose | Access |
|---------|-------------|---------|--------|
| `/db_status` | Check database connection and show statistics | Health check | Admin only |
| `/db_test` | Test all database operations | Functionality test | Admin only |

---

## 🔄 **Typical User Flow**

### **Starting a Tutoring Session:**
1. `/start_session` - Begin tutoring (creates a dedicated thread)
2. `/ask <your question>` - Ask questions (or just type in the thread)
3. `/resume_session` - Resume if session gets disconnected
4. `/end_session` - End when finished
5. `/feedback <1-5>` - Rate your experience

### **Admin/Debug Flow:**
- `/ping` - Check bot responsiveness
- `/db_status` - View database health and statistics
- `/db_test` - Test database functionality
- `/pending_feedback` - Monitor who needs to submit feedback

---

## 📊 **Command Statistics**
- **Total Commands:** 10 slash commands
- **Core Commands:** 2
- **Tutoring Commands:** 4
- **Feedback Commands:** 2
- **Database Commands:** 2

---

## 🛠️ **Technical Details**

### **Database Collections:**
- `users` - User information and registration
- `messages` - Message logs for analysis
- `sessions` - Tutoring session tracking
- `feedback` - User ratings and feedback
- `conversations` - AI conversation history with context

### **AI Integration:**
- **Model:** Gemini-1.5-Flash (LearnLM)
- **Purpose:** Educational tutoring responses
- **Context:** Maintains conversation history for better responses
- **Features:** Message chunking for long responses, thinking indicators

### **Session Management:**
- **Threading:** Creates dedicated Discord threads for each session
- **Auto-timeout:** 10 minutes of inactivity
- **Resume capability:** Can reconnect to existing sessions
- **Context preservation:** Maintains conversation history
- **Feedback requirement:** Required after each session

### **Message Handling:**
- **Thread integration:** Users can type directly in session threads
- **Slash commands:** Traditional command interface
- **Long message support:** Automatic chunking for responses over 2000 characters
- **Thinking indicators:** Shows when AI is processing

---

## 🔧 **Error Handling & Validation**
- Sessions must be started before asking questions
- Resume only works with existing active sessions
- Ratings must be between 1-5
- Database errors are caught and reported with detailed embeds
- Inactive sessions auto-close with user notifications
- Admin commands restricted to users with administrator permissions

---

## 🔒 **Permissions & Access**
- **General Users:** All tutoring and feedback commands
- **Administrators:** Database management commands
- **Thread Access:** Automatic for session participants

---

## 🚀 **New Features**
- **Session Resume:** `/resume_session` allows users to reconnect to existing sessions
- **Direct Thread Messaging:** Users can chat directly in session threads without slash commands
- **Enhanced Database Testing:** Comprehensive database operation validation
- **Improved Error Messages:** Detailed feedback for all error conditions

---

*Last Updated: January 2025*
*Bot Version: 2.0*
