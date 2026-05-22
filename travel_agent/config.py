import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
MODEL_NAME: str = os.getenv("MODEL_NAME", "anthropic/claude-sonnet-4-5")
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
