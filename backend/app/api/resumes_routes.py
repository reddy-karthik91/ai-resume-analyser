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
    Route handler to process an already uploaded resume document (analyzing it via AI).
    
    Provides a synchronous execution mapping to the complete AI workflow.
    """
    # Retrieve pipeline orchestrator from extension registry composition root
    pipeline = current_app.extensions["resume_pipeline"]

    # Analyze and format the resume using the pipeline
    analysis_result = pipeline.analyze_resume(str(document_id))

    # Serialize DTO aggregate recursively
    serialized_result = asdict(analysis_result)
    
    # Convert custom classes/types to standard JSON serializable string formats
    serialized_result["document_id"] = str(serialized_result["document_id"])
    serialized_result["ats_score"]["grade"] = serialized_result["ats_score"]["grade"].value
    serialized_result["summary"]["professional_level"] = serialized_result["summary"]["professional_level"].value
    serialized_result["analysis_status"] = serialized_result["analysis_status"].value
    
    for r in serialized_result["recommendations"]:
        r["priority"] = r["priority"].value
        r["category"] = r["category"].value
        
    serialized_result["analysis_metadata"]["analysis_timestamp"] = serialized_result["analysis_metadata"]["analysis_timestamp"].isoformat() + "Z"

    # Construct standard response envelope
    response_payload = {
        "success": True,
        "message": "Resume analyzed successfully.",
        "data": serialized_result,
        "errors": None,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    return jsonify(response_payload), 200
