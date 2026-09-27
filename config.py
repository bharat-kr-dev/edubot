"""
Configuration Module for Telegram Quiz Bot.
Loads and validates the Telegram Bot Token and optional network settings safely from .env.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the current directory
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# Retrieve configuration from environment variables
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
HTTP_PROXY: str = os.getenv("HTTP_PROXY", "").strip() or os.getenv("HTTPS_PROXY", "").strip()

# Network Timeout Settings (in seconds)
CONNECT_TIMEOUT: float = float(os.getenv("CONNECT_TIMEOUT", "30.0"))
READ_TIMEOUT: float = float(os.getenv("READ_TIMEOUT", "30.0"))
BOOTSTRAP_RETRIES: int = int(os.getenv("BOOTSTRAP_RETRIES", "5"))


def validate_config() -> None:
    """
    Validates that the Telegram bot token is configured properly.
    Exits gracefully with helpful instructions if missing or set to placeholder.
    """
    placeholders = {
        "",
        "your_telegram_bot_token",
        "your_telegram_bot_token_here",
        "xxx",
        "none",
    }

    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN.lower() in placeholders:
        print(
            "\n"
            "==================================================================\n"
            "❌ CONFIGURATION ERROR: Telegram Bot Token is missing!\n"
            "==================================================================\n"
            "1. Open Telegram and search for @BotFather.\n"
            "2. Send /newbot to create your bot and copy the API Token.\n"
            "3. Open the '.env' file in this project folder and set:\n\n"
            "   TELEGRAM_BOT_TOKEN=your_copied_token_here\n\n"
            "4. Run python main.py again.\n"
            "==================================================================\n",
            file=sys.stderr,
        )
        sys.exit(1)
