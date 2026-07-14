from datetime import datetime
from dataclasses import asdict
from flask import Blueprint, request, jsonify, current_app
from app.schemas.upload_response import UploadResponseSchema
from app.exceptions.validation_exceptions import ValidationException

resumes_bp = Blueprint("resumes", __name__)

@resumes_bp.route("/api/v1/resumes/upload", methods=["POST"])
def upload_resume():
    """
    Route handler to accept a resume PDF upload via multipart/form-data,
    validate it, store it securely, and return standard response metadata.
    """
    # Quick check for the file in the request
    if 'file' not in request.files:
        raise ValidationException(
            message="File is required",
            errors=["No file part in request"]
        )

    file = request.files['file']
    
    if file.filename == '':
        raise ValidationException(
            message="File is required",
            errors=["No selected file"]
        )

    # Retrieve pipeline orchestrator from extension registry composition root
    pipeline = current_app.extensions["resume_pipeline"]

    # Orchestrate validation and saving via the ResumeAnalysisPipeline
    metadata = pipeline.upload_resume(file)

    # Format output according to standard API contract
    response_schema = UploadResponseSchema(
        message="Resume uploaded successfully.",
        data=metadata
    )

    return jsonify(response_schema.to_dict()), 201


@resumes_bp.route("/api/v1/resumes/<string:document_id>/process", methods=["POST"])
def process_resume(document_id):
    """
    Route handler to process an already uploaded resume document (by parsing it).
    
    Provides a synchronous execution placeholder mapping to the target AI workflow.
    """
    # Retrieve pipeline orchestrator from extension registry composition root
    pipeline = current_app.extensions["resume_pipeline"]

    # Parse and extract text using the pipeline
    parsed_doc = pipeline.parse_resume(str(document_id))

    # Serialize DTO aggregate recursively
    serialized_doc = asdict(parsed_doc)
    
    # Convert custom classes/types to standard JSON serializable string formats
    serialized_doc["document_id"] = str(serialized_doc["document_id"])
    serialized_doc["document_type"] = serialized_doc["document_type"].value

    # Construct standard response envelope
    response_payload = {
        "success": True,
        "message": "Resume parsed successfully.",
        "data": serialized_doc,
        "errors": None,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    return jsonify(response_payload), 200
