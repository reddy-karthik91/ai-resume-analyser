import os
from dotenv import load_dotenv

# Load environment variables from .env file with explicit absolute path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(base_dir, ".env")
load_dotenv(dotenv_path=dotenv_path)

class Config:
    """Base configuration settings loaded from environment variables."""
    SECRET_KEY = os.getenv("SECRET_KEY", "default-dev-key")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    PORT = int(os.getenv("PORT", 5001))
    ENV = os.getenv("FLASK_ENV", "development")
    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER",
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "uploads"
        )
    )
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    DEFAULT_LLM_MODEL = os.getenv(
        "DEFAULT_LLM_MODEL",
        "llama-3.3-70b-versatile" if LLM_PROVIDER == "groq" else "gemini-2.0-flash"
    )
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.1))
    LLM_TOP_P = float(os.getenv("LLM_TOP_P", 0.95))
    LLM_MAX_OUTPUT_TOKENS = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", 4096))
    LLM_PROMPT_VERSION = os.getenv("LLM_PROMPT_VERSION", "v1.0.0")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", 60))
    LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", 2))
    LLM_RETRY_DELAY_SECONDS = int(os.getenv("LLM_RETRY_DELAY_SECONDS", 2))


class DevelopmentConfig(Config):
    """Development environment specific configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production environment specific configuration."""
    DEBUG = False

# Mapping of environment names to configuration classes
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
