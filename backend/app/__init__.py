import os
from dotenv import load_dotenv

# Load environment variables prior to internal configuration imports
load_dotenv()

from flask import Flask
from flask_cors import CORS

from app.config.settings import config_by_name
from app.routes.health_routes import health_bp

def create_app(config_name=None):
    """Flask Application Factory.
    
    Instantiates and configures the Flask application instance, enables CORS,
    and registers blueprints.
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    
    # Load configuration settings
    config_object = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_object)

    # Enable Cross-Origin Resource Sharing (CORS) for frontend integration
    CORS(app)

    # Register application blueprints
    app.register_blueprint(health_bp)

    return app
