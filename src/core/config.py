"""
Lab 11 — Configuration & API Key Setup
"""
import os

from dotenv import load_dotenv


load_dotenv()
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
ADK_MODEL = f"openai/{OPENAI_MODEL}"


def setup_api_key():
    """Load the OpenAI API key from the environment or prompt."""
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = input("Enter OpenAI API Key: ").strip()
    if not os.environ["OPENAI_API_KEY"]:
        raise RuntimeError("OPENAI_API_KEY is required.")
    print("OpenAI API key loaded.")


# Allowed banking topics (used by topic_filter)
ALLOWED_TOPICS = [
    "banking", "account", "transaction", "transfer",
    "loan", "interest", "savings", "credit",
    "deposit", "withdrawal", "balance", "payment",
    "tai khoan", "giao dich", "tiet kiem", "lai suat",
    "chuyen tien", "the tin dung", "so du", "vay",
    "ngan hang", "atm",
]

# Blocked topics (immediate reject)
BLOCKED_TOPICS = [
    "hack", "exploit", "weapon", "drug", "illegal",
    "violence", "gambling", "bomb", "kill", "steal",
]
