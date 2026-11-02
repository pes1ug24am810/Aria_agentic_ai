import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# App Configurations
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "127.0.0.1")

def has_keys():
    return bool(GROQ_API_KEY and ANTHROPIC_API_KEY)
