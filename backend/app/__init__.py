import os
from dotenv import load_dotenv

# Load environment variables prior to internal configuration imports
load_dotenv()

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from app.config.settings import config_by_name
from app.api.health_routes import health_bp
from app.api.resumes_routes import resumes_bp
from app.exceptions.api_exceptions import APIException
from app.schemas.error_response import ErrorResponseSchema

def create_app(config_name=None):
    """Flask Application Factory.
    
    Instantiates and configures the Flask application instance, enables CORS,
    registers blueprints, and configures global error handlers.
    """
    import sys
    import logging

    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)]
        )

    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    
    # Load configuration settings
    config_object = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_object)

    # Enable Cross-Origin Resource Sharing (CORS) for frontend integration
    CORS(app)

    # Import and compose backend services and repositories (Composition Root)
    from app.repositories.document.filesystem_document_repository import FilesystemDocumentRepository
    from app.services.file_storage_service import FileStorageService
    from app.services.upload_service import UploadService
    from app.services.pdf_parser_service import PdfParserService
    from app.services.resume_analysis_pipeline import ResumeAnalysisPipeline

    repository = FilesystemDocumentRepository()
    storage_service = FileStorageService(repository=repository)
    upload_service = UploadService(storage_service=storage_service)
    parser_service = PdfParserService()

    pipeline = ResumeAnalysisPipeline(
        repository=repository,
        parser_service=parser_service,
        upload_service=upload_service
    )

    # Register composed orchestrator pipeline in the standard Flask extension registry
    app.extensions["resume_pipeline"] = pipeline

    # Register application blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(resumes_bp)

    # Register global error handlers
    @app.errorhandler(APIException)
    def handle_api_exception(error):
        """Handle custom API exceptions and return standardized error payload."""
        errors_list = getattr(error, "errors", [])
        if not errors_list:
            errors_list = [error.message]
            
        error_schema = ErrorResponseSchema(
            message=error.message,
            errors=errors_list
        )
        return jsonify(error_schema.to_dict()), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle standard HTTP errors (e.g. 404, 405) and return standardized error payload."""
        error_schema = ErrorResponseSchema(
            message=error.description,
            errors=[error.description]
        )
        return jsonify(error_schema.to_dict()), error.code

    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Handle unhandled server exceptions and return standardized error payload."""
        app.logger.error(f"Unhandled Exception: {str(error)}", exc_info=True)
        
        errors_list = [str(error)] if app.debug else ["An unexpected server error occurred."]
        error_schema = ErrorResponseSchema(
            message="An unexpected server error occurred.",
            errors=errors_list
        )
        return jsonify(error_schema.to_dict()), 500

    return app

