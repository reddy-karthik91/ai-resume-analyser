import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration settings loaded from environment variables."""
    SECRET_KEY = os.getenv("SECRET_KEY", "default-dev-key")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    PORT = int(os.getenv("PORT", 5001))
    ENV = os.getenv("FLASK_ENV", "development")

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
