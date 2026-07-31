import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from codebase/backend or root
env_path_backend = Path(__file__).parent / ".env"
env_path_root = Path(__file__).parent.parent.parent / ".env"

if env_path_backend.exists():
    load_dotenv(dotenv_path=env_path_backend)
elif env_path_root.exists():
    load_dotenv(dotenv_path=env_path_root)
else:
    load_dotenv()

class Config:
    # Groq API Settings
    GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_KEY") or ""
    GROQ_FALLBACK_API_KEY = os.getenv("GROQ_FALLBACK_API_KEY") or GROQ_API_KEY
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_FALLBACK_MODEL = os.getenv("GROQ_FALLBACK_MODEL", "llama-3.3-70b-lite")

    # Gemini API Settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_FALLBACK_API_KEY") or ""
    GEMINI_PRIMARY_MODEL = os.getenv("GEMINI_PRIMARY_MODEL") or os.getenv("GEMINI_MODEL") or "gemini-1.5-flash"
    GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL") or "gemini-1.5-flash-8b"

    # General API Settings
    DEFAULT_LEARNER_LEVEL = "coban" # coban, thongthao, nangcao
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "15"))

config = Config()
