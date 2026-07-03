from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)

@health_bp.route("/api/v1/health", methods=["GET"])
def check_health():
    """Health check endpoint to verify system status and availability."""
    return jsonify({
        "status": "healthy",
        "application": "AI Resume Analyzer API",
        "version": "1.0.0"
    }), 200
