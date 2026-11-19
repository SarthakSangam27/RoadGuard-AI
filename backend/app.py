import os
import time

from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

from backend.services.detection_service import scan_image, get_model
from backend.database import get_db_connection

load_dotenv()

app = Flask(__name__)
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "message": "RoadGuard-AI Backend is running",
        "status": "healthy"
    }), 200
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

allowed_origins = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [origin.strip() for origin in allowed_origins.split(",") if origin.strip()]
        }
    },
)


def _json_safe_model_result(result):
    """Keep the detection-service response intact while ensuring it is a dict."""
    if isinstance(result, dict):
        return result
    raise ValueError("The detection service returned an invalid response.")


@app.get("/api/health")
def health():
    # Keep this path aligned with the model path configured in detection_service.py.
    model_path = os.path.join(
        os.path.dirname(__file__),
        "models",
        "pothole_best.pt",
    )

    return jsonify(
        {
            "status": "OK",
            "service": "RoadGuard-AI API",
            "ml_model": "available" if os.path.isfile(model_path) else "check_detection_service",
        }
    ), 200


@app.post("/api/scan")
def scan():
    if "image" not in request.files:
        return jsonify({"error": "Upload an image using the 'image' field."}), 400

    uploaded_file = request.files["image"]

    if not uploaded_file.filename:
        return jsonify({"error": "No image selected."}), 400

    image_bytes = uploaded_file.read()
    if not image_bytes:
        return jsonify({"error": "The uploaded file is empty."}), 400

    try:
        scan_started = time.perf_counter()
        result = _json_safe_model_result(scan_image(image_bytes))
        total_processing_time_ms = (time.perf_counter() - scan_started) * 1000.0

        # Preserve all fields returned by detection_service.scan_image().
        # Add total timing without overwriting model-specific timings, if the
        # detection service already returns them.
        response_data = dict(result)
        response_data.setdefault(
            "processing_time_ms",
            round(total_processing_time_ms, 2),
        )
        response_data.setdefault(
            "processing_time_sec",
            round(total_processing_time_ms / 1000.0, 3),
        )

        # These flags help the frontend distinguish an actual dual-model
        # response from a response that contains only one model's output.
        response_data.setdefault(
            "comparison_available",
            isinstance(response_data.get("yolov8"), dict)
            and isinstance(response_data.get("vgg19"), dict),
        )

        return jsonify(response_data), 200

    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except FileNotFoundError:
        app.logger.exception("Model weights are missing")
        return jsonify({"error": "Pothole model weights are unavailable."}), 500
    except Exception:
        app.logger.exception("Image scanning failed")
        return jsonify(
            {"error": "Image scanning failed. Check the backend logs."}
        ), 500


@app.errorhandler(413)
def request_too_large(error):
    return jsonify(
        {"error": "File too large. Maximum upload size is 8 MB."}
    ), 413


@app.post("/api/hazards")
def create_hazard():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Send a JSON object."}), 400

    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if latitude is None or longitude is None:
        return jsonify({"error": "latitude and longitude are required."}), 400

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return jsonify({"error": "latitude and longitude must be numbers."}), 400

    if not (-90 <= latitude <= 90):
        return jsonify({"error": "Invalid latitude."}), 400

    if not (-180 <= longitude <= 180):
        return jsonify({"error": "Invalid longitude."}), 400

    severity = data.get("severity", "medium")
    allowed_severities = {"low", "medium", "high", "critical"}

    if not isinstance(severity, str) or severity not in allowed_severities:
        return jsonify(
            {"error": "severity must be low, medium, high, or critical."}
        ), 400

    confidence = data.get("confidence")
    if confidence is not None:
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            return jsonify({"error": "confidence must be a number."}), 400

        if not 0 <= confidence <= 1:
            return jsonify(
                {"error": "confidence must be between 0 and 1."}
            ), 400

    description = data.get("description")

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO hazards
                        (latitude, longitude, severity, confidence,
                         description, location)
                    VALUES (
                        %s, %s, %s, %s, %s,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                    )
                    RETURNING id, latitude, longitude, severity,
                              confidence, description, created_at
                    """,
                    (
                        latitude,
                        longitude,
                        severity,
                        confidence,
                        description,
                        longitude,
                        latitude,
                    ),
                )
                row = cur.fetchone()

        return jsonify(
            {
                "message": "Hazard saved successfully.",
                "hazard": {
                    "id": row[0],
                    "latitude": row[1],
                    "longitude": row[2],
                    "severity": row[3],
                    "confidence": row[4],
                    "description": row[5],
                    "created_at": row[6].isoformat(),
                },
            }
        ), 201

    except Exception:
        app.logger.exception("Failed to save hazard")
        return jsonify({"error": "Could not save hazard."}), 500


@app.get("/api/hazards")
def get_hazards():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, latitude, longitude, severity,
                           confidence, description, created_at
                    FROM hazards
                    ORDER BY created_at DESC
                    LIMIT 500
                    """
                )
                rows = cur.fetchall()

        hazards = [
            {
                "id": row[0],
                "latitude": row[1],
                "longitude": row[2],
                "severity": row[3],
                "confidence": row[4],
                "description": row[5],
                "created_at": row[6].isoformat(),
            }
            for row in rows
        ]

        return jsonify({"hazards": hazards, "count": len(hazards)}), 200

    except Exception:
        app.logger.exception("Failed to retrieve hazards")
        return jsonify({"error": "Could not retrieve hazards."}), 500


@app.post("/api/reports")
def create_report():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Send a JSON object."}), 400

    hazard_id = data.get("hazard_id")
    description = data.get("report_description")
    authority_name = data.get("authority_name")

    if hazard_id is None:
        return jsonify({"error": "hazard_id is required."}), 400

    try:
        hazard_id = int(hazard_id)
        if hazard_id <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "hazard_id must be a positive integer."}), 400

    if description is not None and not isinstance(description, str):
        return jsonify({"error": "report_description must be text."}), 400

    if authority_name is not None and not isinstance(authority_name, str):
        return jsonify({"error": "authority_name must be text."}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM hazards WHERE id = %s",
                    (hazard_id,),
                )
                if cur.fetchone() is None:
                    return jsonify({"error": "Hazard not found."}), 404

                cur.execute(
                    """
                    INSERT INTO authority_reports
                        (hazard_id, authority_name, report_description)
                    VALUES (%s, %s, %s)
                    RETURNING id, hazard_id, authority_name,
                              report_status, report_description,
                              reported_at, updated_at
                    """,
                    (hazard_id, authority_name, description),
                )
                row = cur.fetchone()

        return jsonify(
            {
                "message": "Authority report created.",
                "report": {
                    "id": row[0],
                    "hazard_id": row[1],
                    "authority_name": row[2],
                    "report_status": row[3],
                    "report_description": row[4],
                    "reported_at": row[5].isoformat(),
                    "updated_at": row[6].isoformat(),
                },
            }
        ), 201

    except Exception:
        app.logger.exception("Failed to create authority report")
        return jsonify({"error": "Could not create report."}), 500


@app.get("/api/reports")
def get_reports():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, hazard_id, authority_name,
                           report_status, report_description,
                           reported_at, updated_at
                    FROM authority_reports
                    ORDER BY reported_at DESC
                    LIMIT 500
                    """
                )
                rows = cur.fetchall()

        reports = [
            {
                "id": row[0],
                "hazard_id": row[1],
                "authority_name": row[2],
                "report_status": row[3],
                "report_description": row[4],
                "reported_at": row[5].isoformat(),
                "updated_at": row[6].isoformat(),
            }
            for row in rows
        ]

        return jsonify({"reports": reports, "count": len(reports)}), 200

    except Exception:
        app.logger.exception("Failed to retrieve authority reports")
        return jsonify({"error": "Could not retrieve reports."}), 500


@app.patch("/api/reports/<int:report_id>")
def update_report(report_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Send a JSON object."}), 400

    status = data.get("report_status")
    allowed_statuses = {
        "pending",
        "submitted",
        "in_progress",
        "resolved",
        "rejected",
    }

    if not isinstance(status, str) or status not in allowed_statuses:
        return jsonify(
            {
                "error": (
                    "report_status must be pending, submitted, "
                    "in_progress, resolved, or rejected."
                )
            }
        ), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE authority_reports
                    SET report_status = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING id, hazard_id, authority_name,
                              report_status, report_description,
                              reported_at, updated_at
                    """,
                    (status, report_id),
                )
                row = cur.fetchone()

                if row is None:
                    return jsonify({"error": "Report not found."}), 404

        return jsonify(
            {
                "message": "Report status updated.",
                "report": {
                    "id": row[0],
                    "hazard_id": row[1],
                    "authority_name": row[2],
                    "report_status": row[3],
                    "report_description": row[4],
                    "reported_at": row[5].isoformat(),
                    "updated_at": row[6].isoformat(),
                },
            }
        ), 200

    except Exception:
        app.logger.exception("Failed to update authority report")
        return jsonify({"error": "Could not update report."}), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
