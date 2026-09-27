# 🤖 Telegram Quiz Bot (Python)

A clean, interactive, and beginner-friendly **Telegram Quiz Bot** built in Python. Designed for students and educators to test their knowledge interactively with inline Telegram buttons, instant answer validation, scoring, explanations, and multi-user support.

---

## 📁 Project Structure

```text
telegram_quiz_agent/
│
├── main.py              # Telegram bot entrypoint, commands, and callback handlers
├── quiz.py              # Question bank, user session state, and scoring logic
├── config.py            # Environment variable loading & validation
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template (safe to commit)
├── .env                 # Your secret Telegram Bot Token (NEVER commit!)
├── .gitignore           # Prevents committing secrets & virtual environments
└── README.md            # Complete setup and usage documentation
```

---

## 🌟 Key Features

- **🚀 Interactive Quizzes**: Multiple-choice questions with clickable inline buttons `[A]`, `[B]`, `[C]`, `[D]`.
- **💡 Instant Explanations**: Immediate feedback upon selecting an option explaining *why* the answer is correct or incorrect.
- **📊 Real-time Scoring & Summary**: Shows total score, percentage, and personalized feedback at the end of every quiz.
- **👥 Multi-User Independent State**: Each Telegram user has their own independent quiz session. One user's answers will never interfere with another's.
- **🔒 Security First**: Bot tokens are loaded via `.env` and kept strictly out of git history.
- **⚡ No External AI API Required**: Runs 100% locally and standalone using standard Python and `python-telegram-bot`.

---

## 🛠️ Prerequisites

- **Python 3.11+** installed on your computer.
- A **Telegram account**.

---

## 📋 Step-by-Step Setup Guide

### 1. Create Your Telegram Bot with BotFather

1. Open the **Telegram** app on your phone or desktop.
2. Search for `@BotFather` (verified bot with a blue checkmark) and click **Start**.
3. Send the command:
   ```text
   /newbot
   ```
4. Follow the prompts:
   - Give your bot a name (e.g., `EduQuiz Student Bot`).
   - Give your bot a username ending in `bot` (e.g., `edu_quiz_demo_bot`).
5. **@BotFather** will reply with your **HTTP API Token**. It looks like:
   ```text
   7123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ1234567
   ```
6. Copy this token safely.

---

### 2. Set Up the Project

#### Clone / Open the Project Folder
Open your terminal (PowerShell / Command Prompt on Windows, or Bash on macOS/Linux) and navigate to the project directory:

```bash
cd d:/edu_bot
```

#### Create a Virtual Environment (Recommended)

**On Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install Dependencies

Install the required Python packages with `pip`:

```bash
pip install -r requirements.txt
```

---

### 4. Configure Your Secret Environment File (`.env`)

1. Copy `.env.example` to `.env` (or create a file named `.env`):
   ```bash
   cp .env.example .env
   ```
2. Open `.env` in your code editor and paste your Telegram Bot Token:
   ```env
   TELEGRAM_BOT_TOKEN=7123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ1234567
   ```

> ⚠️ **SECURITY WARNING:**
> Never share your `.env` file or paste your bot token into public GitHub repositories or chatrooms. The `.gitignore` file is configured to keep your `.env` safe.

---

### 5. Run the Bot

Start the bot by executing:

```bash
python main.py
```

You should see output similar to:
```text
==================================================
🤖 Telegram Quiz Bot is starting...
✅ Configuration validated.
🚀 Polling for messages. Press Ctrl+C to stop.
==================================================
```

---

## 📱 How to Use in Telegram

Open Telegram, search for your bot username, and send:

| Command | Action |
| :--- | :--- |
| `/start` | Displays welcome screen with quick-start button |
| `/quiz` | Starts a 5-question multiple choice quiz |
| `/help` | Displays command list and instructions |

### Interactive Flow Example:
```text
[Bot] 📝 Question 1/5
      What is the result of 2 ** 3 in Python?
      [A] 5
      [B] 6
      [C] 8
      [D] 9

[User clicks [C] 8]

[Bot] ✅ Correct!
      💡 In Python, '**' is the exponentiation operator. 2 ** 3 = 8.

[Bot automatically sends Question 2/5...]
```

When all 5 questions are complete:
```text
🎉 Quiz Completed!

📊 Score: 4/5
📈 Percentage: 80.0%

💬 Great job! 👍 You have a strong grasp of Python basics!

[🔄 Start Again]
```

---

## ✏️ How to Add or Edit Questions

All quiz questions are stored in `quiz.py` under `QUESTIONS_DATABASE`.

To add a new question, simply add a new dictionary to the list:

```python
{
    "question": "What is the keyword to create a loop over items in Python?",
    "options": ["while", "for", "loop", "iterate"],
    "answer": "for",
    "explanation": "The 'for' keyword in Python is used to iterate over a sequence (such as a list or range)."
}
```

- Ensure `options` has 4 choices.
- Ensure `answer` matches one of the `options` exactly.
- Provide a helpful `explanation`.

---

## 🧠 Architecture & How It Works

### Architecture Diagram
```text
┌─────────────────┐
│  Telegram User  │
└────────┬────────┘
         │ (Sends /quiz or clicks [A]/[B]/[C]/[D])
         ▼
┌─────────────────────────────────┐
│   Telegram Cloud Servers (API)  │
└────────┬────────────────────────┘
         │ (HTTPS Polling)
         ▼
┌─────────────────────────────────┐
│        main.py (Handlers)       │
│  - /start, /help, /quiz         │
│  - CallbackQueryHandler (ans_x) │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│        quiz.py (State Store)    │
│  - Tracks user_id -> Session    │
│  - Questions, Score, Feedback   │
└─────────────────────────────────┘
```

### Multi-User State Isolation
The bot tracks active quizzes inside a Python dictionary keyed by each user's unique Telegram User ID:
```python
_USER_SESSIONS: Dict[int, QuizSession] = {}
```
This guarantees that Alice's answers and Bob's answers are completely isolated from each other.

---

## 🛡️ Troubleshooting & FAQs

1. **Error: `Telegram Bot Token is missing!`**
   - Ensure you created a `.env` file and set `TELEGRAM_BOT_TOKEN=...` without extra quotes or spaces.
2. **Bot is not responding to commands:**
   - Make sure `python main.py` is running in your terminal.
   - Check if you clicked `Start` in Telegram on your bot's chat.
3. **Double Click Prevention:**
   - Buttons are automatically cleared after clicking an option to prevent accidental double-submitting.
