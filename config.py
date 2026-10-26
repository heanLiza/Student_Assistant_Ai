"""Central configuration. The API key is read from the environment only."""
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
# Tried in order if the main model fails (timeout / overloaded / not found)
FALLBACK_MODELS = [m.strip() for m in os.getenv(
    "GEMINI_FALLBACKS",
    "gemini-flash-lite-latest,gemini-2.5-flash-lite,gemini-3.8-flash").split(",") if m.strip()]
DEMO_MODE = os.getenv("DEMO_MODE", "0") == "1"   # sample data only (offline UI test)
PER_CALL_TIMEOUT_MS = 25000     # one model attempt
TOTAL_BUDGET_SECONDS = 80       # all attempts together
MAX_OUTPUT_TOKENS = 4096
MAX_INPUT_CHARS = 15000         # what the user may enter
MODEL_INPUT_CHARS = 8000        # what is sent to the AI (shorter = faster)
MIN_INPUT_CHARS = 20
MIN_ITEMS, MAX_ITEMS, DEFAULT_ITEMS = 1, 15, 5
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
TASKS = ("explain", "summarize", "flashcards", "quiz", "practice")
JSON_TASKS = ("flashcards", "quiz", "practice")
LANGUAGES = {"auto": "the same language as the lesson", "km": "Khmer", "en": "English"}
