"""
Central configuration for Brand Visibility Agent.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load config/.env if present, otherwise default dotenv loading
_config_env = Path(__file__).parent / ".env"
if _config_env.exists():
    load_dotenv(_config_env)
else:
    load_dotenv()

REAL_MODE = False
FIRE_CRAWL_ENABLED = False
OPERATOR_NAME = "Anshu"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

AI_REQUEST_TIMEOUT = int(os.getenv("AI_REQUEST_TIMEOUT", "15"))
AI_MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "1"))
AI_RETRY_BACKOFF_SECONDS = int(os.getenv("AI_RETRY_BACKOFF_SECONDS", "2"))
AI_MAX_REAL_CALLS_PER_RUN = int(os.getenv("AI_MAX_REAL_CALLS_PER_RUN", "10"))
AI_CONSECUTIVE_FAILURE_LIMIT = int(os.getenv("AI_CONSECUTIVE_FAILURE_LIMIT", "3"))
