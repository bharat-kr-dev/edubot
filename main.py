"""
Main Telegram Bot Entrypoint.
Initializes the Telegram Bot, registers command & callback handlers,
manages user interactions with inline keyboards, and maintains quiz flow.
Configured with robust network retry and timeout handling.
"""

import logging
from typing import Optional

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.request import HTTPXRequest

import config
import quiz

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ==============================================================================
# Helper UI Functions
# ==============================================================================
def build_question_keyboard(options: list[str]) -> InlineKeyboardMarkup:
    """Creates inline keyboard buttons for question options."""
    labels = ["A", "B", "C", "D"]
    keyboard = []

    for idx, opt in enumerate(options):
        prefix = labels[idx] if idx < len(labels) else f"#{idx+1}"
        button_text = f"[{prefix}] {opt}"
        # Store the option index in callback_data to keep payload small and reliable
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"ans_{idx}")])

    return InlineKeyboardMarkup(keyboard)


async def send_current_question(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
    """Formats and sends the current question to the user with inline option buttons."""
    session = quiz.get_user_session(user_id)
    if not session or session.is_finished:
        return

    q_data = session.get_current_question()
    if not q_data:
        return

    q_num = session.current_index + 1
    total_q = session.total_questions

    message_text = (
        f"📝 <b>Question {q_num}/{total_q}</b>\n\n"
        f"<b>{q_data['question']}</b>"
    )

    reply_markup = build_question_keyboard(q_data["options"])

    if update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    elif update.message:
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )


async def send_final_results(query, user_id: int) -> None:
    """Calculates and displays the final score card, percentage, feedback, and restart button."""
    session = quiz.get_user_session(user_id)
    if not session:
        return

    score = session.score
    total = session.total_questions
    percentage = quiz.calculate_percentage(score, total)
    feedback = quiz.get_feedback_message(percentage)

    result_text = (
        f"🎉 <b>Quiz Completed!</b>\n\n"
        f"📊 <b>Score:</b> {score}/{total}\n"
        f"📈 <b>Percentage:</b> {percentage}%\n\n"
        f"💬 <i>{feedback}</i>"
    )

    restart_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Start Again", callback_data="restart_quiz")]
    ])

    if query.message:
        await query.message.reply_text(
            text=result_text,
            reply_markup=restart_keyboard,
            parse_mode="HTML"
        )

    # Clean up user session
    quiz.clear_user_session(user_id)


# ==============================================================================
# Command Handlers
# ==============================================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /start command: greets the user and shows available actions."""
    if not update.message:
        return

    user_first_name = update.effective_user.first_name if update.effective_user else "Student"

    welcome_text = (
        f"👋 Welcome {user_first_name} to <b>AI Edublink Quiz Agent</b>!\n\n"
        "I can conduct an interactive quiz for you.\n\n"
        "<b>Commands:</b>\n"
        "• /quiz - Start a quiz\n"
        "• /help - Show help"
    )

    start_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Start Quiz Now", callback_data="restart_quiz")]
    ])

    await update.message.reply_text(
        text=welcome_text,
        reply_markup=start_keyboard,
        parse_mode="HTML"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /help command: provides instructions and explanations."""
    if not update.message:
        return

    help_text = (
        "💡 <b>EduBlink Quiz Bot Help Guide</b>\n\n"
        "<b>How to use:</b>\n"
        "1. Send /quiz to begin a 5-question Python quiz.\n"
        "2. Click the inline buttons [A], [B], [C], or [D] to submit your answer.\n"
        "3. You will immediately see if your choice was correct along with an explanation.\n"
        "4. After 5 questions, your final score and performance feedback will be displayed.\n"
        "5. Click <b>🔄 Start Again</b> or send /quiz to retry anytime!\n\n"
        "<b>Available Commands:</b>\n"
        "/quiz - Start a new quiz session\n"
        "/help - Display this help guide\n"
        "/start - Welcome screen"
    )

    await update.message.reply_text(
        text=help_text,
        parse_mode="HTML"
    )


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /quiz command: initiates a new quiz for the user."""
    if not update.effective_user or not update.message:
        return

    user_id = update.effective_user.id
    quiz.start_new_quiz_session(user_id=user_id, num_questions=5)

    await update.message.reply_text(
        "🚀 <b>Starting your Python Quiz!</b>\nGet ready for 5 questions...",
        parse_mode="HTML"
    )
    await send_current_question(update, context, user_id)


# ==============================================================================
# Callback Query Handler (Inline Button Clicks)
# ==============================================================================
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles button clicks for answering questions and restarting quizzes."""
    query = update.callback_query
    if not query or not update.effective_user:
        return

    await query.answer()  # Acknowledge the button click to Telegram
    user_id = update.effective_user.id
    callback_data = query.data or ""

    # Handle Restart Quiz
    if callback_data == "restart_quiz":
        quiz.start_new_quiz_session(user_id=user_id, num_questions=5)
        if query.message:
            await query.message.reply_text(
                "🔄 <b>New Quiz Started!</b>\nHere is your first question:",
                parse_mode="HTML"
            )
        await send_current_question(update, context, user_id)
        return

    # Handle Answer Selection
    if callback_data.startswith("ans_"):
        session = quiz.get_user_session(user_id)

        # If no active session found
        if not session or not session.is_active:
            if query.message:
                await query.message.reply_text(
                    "⚠️ This quiz session has expired or finished.\nSend /quiz to start a new one!",
                    parse_mode="HTML"
                )
            return

        current_q = session.get_current_question()
        if not current_q:
            await send_final_results(query, user_id)
            return

        # Parse selected option index
        try:
            opt_idx = int(callback_data.split("_")[1])
            selected_option = current_q["options"][opt_idx]
        except (IndexError, ValueError):
            return

        # Record answer and update session score
        is_correct, correct_answer, explanation = session.submit_answer(selected_option)

        # Disable buttons on the answered message to prevent double clicking
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass

        # Build feedback message
        if is_correct:
            result_header = "✅ <b>Correct!</b>"
        else:
            result_header = f"❌ <b>Incorrect!</b>\nCorrect answer: <b>{correct_answer}</b>"

        feedback_text = (
            f"{result_header}\n\n"
            f"💡 <i>{explanation}</i>"
        )

        if query.message:
            await query.message.reply_text(
                text=feedback_text,
                parse_mode="HTML"
            )

        # Check if more questions remain
        if not session.is_finished:
            await send_current_question(update, context, user_id)
        else:
            await send_final_results(query, user_id)


# ==============================================================================
# Global Error Handler
# ==============================================================================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates and notify user without crashing the bot."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ An unexpected error occurred while processing your request. Please try again."
            )
        except Exception:
            pass


# ==============================================================================
# Application Startup
# ==============================================================================
def main() -> None:
    """Validates configuration and launches the Telegram Bot polling loop."""
    # Validate .env settings
    config.validate_config()

    print("==================================================")
    print("🤖 Telegram Quiz Bot is starting...")
    print("✅ Configuration validated.")
    print("🚀 Connecting to Telegram servers...")
    print("==================================================")

    # Configure robust HTTP request client with higher timeouts & optional proxy
    request_kwargs = {
        "connect_timeout": config.CONNECT_TIMEOUT,
        "read_timeout": config.READ_TIMEOUT,
        "write_timeout": 30.0,
        "pool_timeout": 30.0,
    }
    if config.HTTP_PROXY:
        request_kwargs["proxy_url"] = config.HTTP_PROXY
        print(f"🌐 Using Proxy: {config.HTTP_PROXY}")

    custom_request = HTTPXRequest(**request_kwargs)

    # Initialize Telegram Application with custom request handler
    application = (
        ApplicationBuilder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .request(custom_request)
        .build()
    )

    # Register Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("quiz", quiz_command))
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Register Error Handler
    application.add_error_handler(error_handler)

    # Start Polling with retry support
    application.run_polling(
        drop_pending_updates=True,
        bootstrap_retries=config.BOOTSTRAP_RETRIES,
        timeout=30,
        read_timeout=config.READ_TIMEOUT,
        write_timeout=30.0,
        connect_timeout=config.CONNECT_TIMEOUT,
        pool_timeout=30.0,
    )


if __name__ == "__main__":
    main()
