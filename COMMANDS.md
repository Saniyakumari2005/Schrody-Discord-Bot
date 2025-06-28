
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
| `/end_session` | End the current tutoring session | Active session |

### **💬 Feedback Commands**
| Command | Description | Parameters |
|---------|-------------|------------|
| `/feedback <rating>` | Submit feedback with a rating | Rating: 1-5 |
| `/pending_feedback` | List users who haven't given feedback yet | None |

### **🗄️ Database Management Commands**
| Command | Description | Purpose |
|---------|-------------|---------|
| `/db_status` | Check database connection and show statistics | Health check |
| `/db_test` | Test all database operations | Functionality test |

---

## 🔄 **Typical User Flow**

### **Starting a Tutoring Session:**
1. `/start_session` - Begin tutoring
2. `/ask <your question>` - Ask questions
3. `/end_session` - End when finished
4. `/feedback <1-5>` - Rate your experience

### **Admin/Debug Flow:**
- `/ping` - Check bot responsiveness
- `/db_status` - View database health
- `/db_test` - Test database functionality
- `/pending_feedback` - Monitor feedback status

---

## 📊 **Command Statistics**
- **Total Commands:** 8 slash commands
- **Core Commands:** 2
- **Tutoring Commands:** 3
- **Feedback Commands:** 2
- **Database Commands:** 2

---

## 🛠️ **Technical Details**

### **Database Collections:**
- `users` - User information
- `messages` - Message logs
- `sessions` - Tutoring sessions
- `feedback` - User ratings
- `conversations` - AI conversation history

### **AI Integration:**
- **Model:** Gemini-1.5-Flash
- **Purpose:** Educational tutoring responses
- **Context:** Maintains conversation history

### **Session Management:**
- **Auto-timeout:** 10 minutes of inactivity
- **Threading:** Creates dedicated threads for sessions
- **Feedback:** Required after each session

---

## 🔧 **Error Handling**
- Sessions must be started before asking questions
- Ratings must be between 1-5
- Database errors are caught and reported
- Inactive sessions auto-close with notifications

---

*Last Updated: [Current Date]*
*Bot Version: 1.0*
