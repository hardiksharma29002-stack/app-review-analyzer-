"""
Centralized configuration for App Review Insights Analyzer.

Loads environment variables from .env, validates required secrets,
and defines all constants used across the pipeline and web app.

Edge cases handled:
    - #39:  GROQ_API_KEY missing → clear error at startup
    - #81:  SMTP env vars missing → clear error before send attempt
    - #119: PORT env var defaults to 8000 for local dev
    - #124: All env vars validated at startup on Render
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env file (only affects local dev; on Render, env vars are set directly)
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMPLATES_DIR = PROJECT_ROOT / "app" / "templates"
STATIC_DIR = PROJECT_ROOT / "app" / "static"

# Ensure output directory exists (Edge Case #78)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Server configuration
# ---------------------------------------------------------------------------
PORT = int(os.getenv("PORT", 8000))  # Edge Case #119: Render provides PORT

# ---------------------------------------------------------------------------
# Groq LLM configuration (Classification)
# ---------------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL_PRIMARY = "llama-3.1-8b-instant"
GROQ_MODEL_FALLBACK = "llama3-8b-8192"

# Classification settings
CLASSIFICATION_BATCH_SIZE = 25          # Reviews per API call
CLASSIFICATION_TEMPERATURE = 0.0        # Deterministic
CLASSIFICATION_MAX_RETRIES = 3          # Retries per batch on rate-limit

# ---------------------------------------------------------------------------
# Gemini LLM configuration (Insights)
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"

# Insight generation settings
INSIGHT_TEMPERATURE = 0.3               # Slightly creative, but grounded
INSIGHT_MAX_RETRIES = 2

# ---------------------------------------------------------------------------
# Theme configuration (Themes are now extracted dynamically per dataset)
# ---------------------------------------------------------------------------# ---------------------------------------------------------------------------
# Report constraints (enforced in code, not just prompts)
# ---------------------------------------------------------------------------
REPORT_MAX_WORDS = 800
REPORT_TOP_THEMES = 3
REPORT_QUOTES_COUNT = 3
REPORT_RECOMMENDATIONS_COUNT = 3
QUOTE_MAX_WORDS = 50

# ---------------------------------------------------------------------------
# Email configuration (Google Apps Script Webhook)
# ---------------------------------------------------------------------------
GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL", "")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "")
EMAIL_SUBJECT = "Weekly Product Review Insights"

# ---------------------------------------------------------------------------
# Review scraper configuration
# ---------------------------------------------------------------------------
GROWW_APP_ID = "com.nextbillion.groww"
DEFAULT_SCRAPE_WEEKS = 8
MAX_REVIEWS_CAP = 2000  # Edge Case #24: cap large datasets at scrape time
MAX_REVIEWS_TO_ANALYZE = 1000  # Cap for pipeline execution to ensure <10s LLM speed

# ---------------------------------------------------------------------------
# STRETCH: Upload constraints
# ---------------------------------------------------------------------------
MAX_UPLOAD_SIZE_MB = 5
MAX_EMAILS_PER_IP_PER_HOUR = 5

# ---------------------------------------------------------------------------
# CSV schema — required columns
# ---------------------------------------------------------------------------
REQUIRED_CSV_COLUMNS = {"rating", "text", "date"}
OPTIONAL_CSV_COLUMNS = {"title"}

# ---------------------------------------------------------------------------
# PII regex patterns (used in clean.py and group_quotes.py)
# ---------------------------------------------------------------------------
PII_PATTERNS = {
    "email": {
        "pattern": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        "replacement": "[EMAIL REDACTED]",
    },
    "phone_indian": {
        "pattern": r"(\+?91[\s\-]?)?[6-9]\d{4}[\s\-]?\d{5}",
        "replacement": "[PHONE REDACTED]",
    },
    "phone_generic": {
        "pattern": r"\b\d{10,12}\b",
        "replacement": "[PHONE REDACTED]",
    },
    "aadhaar": {
        "pattern": r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b",
        "replacement": "[ID REDACTED]",
    },
    "pan_card": {
        "pattern": r"\b[A-Z]{5}\d{4}[A-Z]\b",
        "replacement": "[ID REDACTED]",
    },
    "url": {
        "pattern": r"https?://\S+",
        "replacement": "[URL REDACTED]",
    },
}


def validate_groq_config() -> tuple[bool, str]:
    """
    Check if Groq API key is configured.

    Returns:
        (is_valid, message)
    """
    if not GROQ_API_KEY:
        return False, (
            "GROQ_API_KEY is not set. "
            "Get your free key at https://console.groq.com/keys "
            "and add it to your .env file."
        )
    if not GROQ_API_KEY.startswith("gsk_"):
        return False, (
            "GROQ_API_KEY appears invalid (should start with 'gsk_'). "
            "Check your .env file."
        )
    return True, "Groq API key is configured."


def validate_gemini_config() -> tuple[bool, str]:
    """
    Check if Gemini API key is configured.
    """
    if not GEMINI_API_KEY:
        return False, "GEMINI_API_KEY is not set in .env."
    return True, "Gemini API key is configured."


def validate_email_config() -> tuple[bool, str]:
    """
    Check if Google Script URL is configured.

    Returns:
        (is_valid, message)
    """
    missing = []
    if not GOOGLE_SCRIPT_URL:
        missing.append("GOOGLE_SCRIPT_URL")

    if missing:
        return False, (
            f"Email not configured. Missing: {', '.join(missing)}. "
            "See .env.example for setup instructions."
        )
    return True, "Email configuration is set."


def validate_all_config() -> dict:
    """
    Validate all configuration at startup.
    Returns a dict of check results for the /health endpoint.
    """
    groq_ok, groq_msg = validate_groq_config()
    gemini_ok, gemini_msg = validate_gemini_config()
    email_ok, email_msg = validate_email_config()
    data_dir_ok = DATA_DIR.exists()
    csv_exists = (DATA_DIR / "reviews.csv").exists()

    return {
        "groq_api": {"ok": groq_ok, "message": groq_msg},
        "gemini_api": {"ok": gemini_ok, "message": gemini_msg},
        "email": {"ok": email_ok, "message": email_msg},
        "data_dir": {"ok": data_dir_ok, "message": "Data directory exists" if data_dir_ok else "Data directory missing"},
        "reviews_csv": {"ok": csv_exists, "message": "reviews.csv found" if csv_exists else "reviews.csv not found (run scraper or upload)"},
    }


if __name__ == "__main__":
    # Quick self-check when run directly
    print("=" * 50)
    print("Configuration Self-Check")
    print("=" * 50)
    checks = validate_all_config()
    all_ok = True
    for name, result in checks.items():
        status = "OK" if result["ok"] else "FAIL"
        print(f"  [{status}] {name}: {result['message']}")
        if not result["ok"]:
            all_ok = False
    print("=" * 50)
    print("All checks passed!" if all_ok else "Some checks failed — see above.")
    sys.exit(0 if all_ok else 1)
