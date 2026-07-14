from flask import Blueprint, request, jsonify
from app.services.resume_analysis_pipeline import ResumeAnalysisPipeline
from app.schemas.upload_response import UploadResponseSchema
from app.exceptions.validation_exceptions import ValidationException

resumes_bp = Blueprint("resumes", __name__)
pipeline = ResumeAnalysisPipeline()

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

    # Orchestrate validation and saving via the ResumeAnalysisPipeline
    metadata = pipeline.upload_resume(file)



    # Format output according to standard API contract
    response_schema = UploadResponseSchema(
        message="Resume uploaded successfully.",
        data=metadata
    )

    return jsonify(response_schema.to_dict()), 201
