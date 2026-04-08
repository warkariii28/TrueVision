import os
import secrets
import traceback
from datetime import timedelta
from typing import Any, cast
from uuid import uuid4

from flask import abort, jsonify, request, send_from_directory, session
from flask_login import current_user, login_user, logout_user
from PIL import Image, UnidentifiedImageError
from sqlalchemy import func
from sqlalchemy.exc import (
    DataError,
    DatabaseError,
    IntegrityError,
    InterfaceError,
    InvalidRequestError,
)
from werkzeug.exceptions import NotFound
from werkzeug.utils import secure_filename

from app import bcrypt, create_app, db, limiter, login_manager
from filter_utils import filter_image
from inference import predict_image
from models import Performance, Result, User


@login_manager.user_loader
def load_user(user_id):
    return db_session.get(User, int(user_id))


app = create_app()
db_session = cast(Any, db.session)
static_root = app.static_folder or os.path.join(os.path.dirname(__file__), "static")


@app.before_request
def session_handler():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=7)


def user_to_dict(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
    }


def ensure_csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def csrf_failure_response():
    return jsonify({"error": "Invalid CSRF token"}), 403


def require_csrf():
    session_token = session.get("csrf_token")
    request_token = request.headers.get("X-CSRF-Token")

    if not session_token or not request_token or session_token != request_token:
        return csrf_failure_response()

    return None


def result_to_dict(result):
    return {
        "id": result.result_id,
        "saved": True,
        "prediction": result.prediction,
        "confidence": result.confidence_score,
        "feedback": result.feedback,
        "imagePath": result.image_path,
        "gradcamPath": result.gradcam_path,
        "explanation": result.explanation,
        "recommendation": result.recommendation,
        "createdAt": result.created_at.isoformat() if result.created_at else None,
        "inferenceTime": result.inference_time,
    }


def guest_result_to_dict(result: dict):
    return {
        "id": None,
        "saved": False,
        "prediction": result["prediction"],
        "confidence": result["confidence"],
        "feedback": None,
        "imagePath": None,
        "gradcamPath": None,
        "explanation": result.get("explanation", ""),
        "recommendation": result.get("recommendation", ""),
        "createdAt": None,
        "inferenceTime": result.get("inference_time"),
    }


def performance_to_dict(performance):
    return {
        "id": performance.id,
        "modelName": performance.model_name,
        "accuracy": performance.accuracy,
        "precision": performance.precision,
        "recall": performance.recall,
        "f1Score": performance.f1_score,
        "fpr": performance.fpr,
        "fnr": performance.fnr,
        "tnr": performance.tnr,
        "tp": performance.tp,
        "tn": performance.tn,
        "fp": performance.fp,
        "fn": performance.fn,
        "aucRoc": performance.auc_roc,
        "prAuc": performance.pr_auc,
        "confusionMatrix": performance.confusion_matrix,
    }


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
ALLOWED_IMAGE_FORMATS = {"PNG", "JPEG"}
MAX_IMAGE_PIXELS = 25_000_000


def allowed_file(filename):
    if "." not in filename:
        return False

    name, ext = os.path.splitext(filename)

    if ext.lower().replace(".", "") not in ALLOWED_EXTENSIONS:
        return False

    if len(name) < 1:
        return False

    return True


def log_and_respond(message: str, error: Exception, status_code: int = 500):
    app.logger.error("%s: %s", message, str(error))
    app.logger.error(traceback.format_exc())
    return jsonify({"error": message}), status_code


def rate_limit_identity(identifier: str) -> str:
    return f"{request.remote_addr or 'unknown'}:{identifier or 'anonymous'}"


def register_rate_limit_key() -> str:
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    username = (data.get("username") or "").strip().lower()
    return rate_limit_identity(email or username or "anonymous")


def login_rate_limit_key() -> str:
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    return rate_limit_identity(email or "anonymous")


def upload_rate_limit_key() -> str:
    identifier = str(current_user.id) if current_user.is_authenticated else "guest"
    return rate_limit_identity(identifier)


def validate_uploaded_image(filepath: str) -> tuple[bool, str | None]:
    try:
        with Image.open(filepath) as image:
            image.verify()

        with Image.open(filepath) as image:
            if image.format not in ALLOWED_IMAGE_FORMATS:
                return False, "Unsupported file type. Please upload a PNG, JPG, or JPEG image."

            width, height = image.size
            if width < 32 or height < 32:
                return False, "The image is too small to analyze reliably. Please upload a clearer face image."

            if width * height > MAX_IMAGE_PIXELS:
                return False, "The image is too large to analyze safely. Please upload a smaller image."

        return True, None

    except (Image.DecompressionBombError, UnidentifiedImageError, OSError):
        return False, "The uploaded file is not a valid PNG or JPEG image."


def is_allowed_media_path(path: str | None) -> bool:
    if not path:
        return False

    normalized = os.path.normpath(path).replace("\\", "/").lstrip("/")
    if normalized.startswith("../") or normalized == "..":
        return False

    return normalized.startswith("uploads/") or normalized.startswith("gradcam/")


def send_media_path(path: str):
    if not is_allowed_media_path(path):
        abort(404)

    normalized = os.path.normpath(path).replace("\\", "/").lstrip("/")
    absolute_path = os.path.join(static_root, normalized)

    if not os.path.isfile(absolute_path):
        abort(404)

    return send_from_directory(static_root, normalized)


# Auth APIs
@app.route("/api/auth/me", methods=["GET"])
def api_auth_me():
    csrf_token = ensure_csrf_token()

    if current_user.is_authenticated:
        return (
            jsonify(
                {
                    "authenticated": True,
                    "user": user_to_dict(current_user),
                    "csrfToken": csrf_token,
                }
            ),
            200,
        )

    return (
        jsonify(
            {
                "authenticated": False,
                "user": None,
                "csrfToken": csrf_token,
            }
        ),
        200,
    )


@app.route("/api/auth/register", methods=["POST"])
@limiter.limit(lambda: app.config["REGISTER_RATE_LIMIT"], key_func=register_rate_limit_key)
def api_auth_register():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Missing request body"}), 400

    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    confirm_password = data.get("confirmPassword") or ""

    if not username or not email or not password or not confirm_password:
        return jsonify({"error": "All fields are required"}), 400

    if password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    try:
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        new_user = User()
        new_user.username = username
        new_user.email = email
        new_user.pwd = hashed_password

        db_session.add(new_user)
        db_session.commit()

        login_user(new_user)
        session.permanent = True
        csrf_token = ensure_csrf_token()

        return (
            jsonify(
                {
                    "message": "Registration successful",
                    "user": user_to_dict(new_user),
                    "csrfToken": csrf_token,
                }
            ),
            201,
        )

    except IntegrityError:
        db_session.rollback()
        return (
            jsonify(
                {
                    "error": "User already exists! Please use a different email or username."
                }
            ),
            409,
        )
    except DataError:
        db_session.rollback()
        return jsonify({"error": "Invalid entry"}), 400
    except InterfaceError:
        db_session.rollback()
        return jsonify({"error": "Database connection error"}), 500
    except DatabaseError:
        db_session.rollback()
        return jsonify({"error": "Database error"}), 500
    except InvalidRequestError:
        db_session.rollback()
        return jsonify({"error": "Something went wrong"}), 500
    except Exception as e:
        db_session.rollback()
        return log_and_respond("Registration failed. Please try again later.", e)


@app.route("/api/auth/login", methods=["POST"])
@limiter.limit(lambda: app.config["LOGIN_RATE_LIMIT"], key_func=login_rate_limit_key)
def api_auth_login():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Missing request body"}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        user = User.query.filter(func.lower(User.email) == email).first()

        if user and bcrypt.check_password_hash(user.pwd, password):
            login_user(user)
            session.permanent = True
            csrf_token = ensure_csrf_token()

            return (
                jsonify(
                    {
                        "message": "Login successful",
                        "user": user_to_dict(user),
                        "csrfToken": csrf_token,
                    }
                ),
                200,
            )

        return jsonify({"error": "Invalid email or password"}), 401

    except Exception as e:
        return log_and_respond("Login failed. Please try again later.", e)


@app.route("/api/auth/logout", methods=["POST"])
def api_auth_logout():
    csrf_error = require_csrf()
    if csrf_error:
        return csrf_error

    if current_user.is_authenticated:
        logout_user()

    session.pop("csrf_token", None)
    session.clear()

    return jsonify({"message": "Logged out successfully"}), 200


# Upload API
@app.route("/api/upload", methods=["POST"])
@limiter.limit(lambda: app.config["UPLOAD_RATE_LIMIT"], key_func=upload_rate_limit_key)
def api_upload():
    csrf_error = require_csrf()
    if csrf_error:
        return csrf_error

    if "file" not in request.files:
        return jsonify({"error": "No file was included in the request"}), 400

    file = request.files["file"]

    incoming_filename = file.filename or ""

    if incoming_filename == "":
        return jsonify({"error": "No file was selected"}), 400

    if not allowed_file(incoming_filename):
        return (
            jsonify(
                {
                    "error": "Unsupported file type. Please upload a PNG, JPG, or JPEG image."
                }
            ),
            400,
        )

    filepath = None

    try:
        original_filename = secure_filename(incoming_filename)
        ext = original_filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid4().hex}.{ext}"

        upload_dir = app.config["UPLOAD_FOLDER"]
        gradcam_dir = app.config["GRADCAM_FOLDER"]
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(gradcam_dir, exist_ok=True)

        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)

        is_valid_image, validation_error = validate_uploaded_image(filepath)
        if not is_valid_image:
            if os.path.exists(filepath):
                os.remove(filepath)

            return jsonify({"error": validation_error}), 400

        if not filter_image(filepath):
            if os.path.exists(filepath):
                os.remove(filepath)

            return (
                jsonify(
                    {
                        "error": "The image was too unclear to analyze. Please use a sharper, well-lit face image."
                    }
                ),
                400,
            )

        result = predict_image(filepath)

        if result is None:
            if os.path.exists(filepath):
                os.remove(filepath)

            return jsonify({"error": "AI processing returned no results."}), 500

        if "error" in result:
            if os.path.exists(filepath):
                os.remove(filepath)

            return jsonify({"error": result["error"]}), 500

        if "prediction" not in result:
            if os.path.exists(filepath):
                os.remove(filepath)

            return (
                jsonify(
                    {"error": "AI processing was incomplete. Missing prediction data."}
                ),
                500,
            )

        image_path = os.path.join("uploads", filename).replace("\\", "/")
        gradcam_rel_path = result.get("gradcam_path", "")

        if current_user.is_authenticated:
            new_result = Result()
            new_result.confidence_score = result["confidence"]
            new_result.prediction = result["prediction"]
            new_result.feedback = None
            new_result.image_path = image_path
            new_result.user_id = current_user.id
            new_result.explanation = result.get("explanation", "")
            new_result.gradcam_path = gradcam_rel_path
            new_result.recommendation = result.get("recommendation", "")
            new_result.inference_time = result.get("inference_time")

            db_session.add(new_result)
            db_session.commit()

            return (
                jsonify(
                    {
                        "message": "Upload processed successfully",
                        "result": result_to_dict(new_result),
                    }
                ),
                201,
            )

        guest_result = {
            "image_path": image_path,
            "gradcam_path": gradcam_rel_path,
            "prediction": result["prediction"],
            "confidence": result["confidence"],
            "explanation": result.get("explanation", ""),
            "recommendation": result.get("recommendation", ""),
            "inference_time": result.get("inference_time"),
        }
        session["guest_result"] = guest_result

        return (
            jsonify(
                {
                    "message": "Upload processed successfully",
                    "result": guest_result_to_dict(guest_result),
                }
            ),
            200,
        )

    except Exception as e:
        db_session.rollback()

        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        return log_and_respond("An error occurred while processing the upload.", e)


# Results APIs
@app.route("/api/results", methods=["GET"])
def api_results():
    if not current_user.is_authenticated:
        return jsonify({"error": "Authentication required"}), 401

    try:
        results = (
            Result.query.filter_by(user_id=current_user.id)
            .order_by(Result.created_at.desc())
            .all()
        )

        return jsonify({"results": [result_to_dict(result) for result in results]}), 200

    except Exception as e:
        return log_and_respond("Failed to load results.", e)


@app.route("/api/results/<int:result_id>", methods=["GET"])
def api_result_detail(result_id):
    if not current_user.is_authenticated:
        return jsonify({"error": "Authentication required"}), 401

    try:
        result = Result.query.filter_by(
            result_id=result_id,
            user_id=current_user.id,
        ).first()

        if not result:
            return jsonify({"error": "Result not found"}), 404

        return jsonify({"result": result_to_dict(result)}), 200

    except Exception as e:
        return log_and_respond("Failed to load result details.", e)


# Feedback API
@app.route("/api/results/<int:result_id>/feedback", methods=["POST"])
def api_submit_feedback(result_id):
    if not current_user.is_authenticated:
        return jsonify({"error": "Authentication required"}), 401

    csrf_error = require_csrf()
    if csrf_error:
        return csrf_error

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Missing request body"}), 400

    feedback = data.get("feedback")

    if feedback not in ["Satisfied", "Unsatisfied"]:
        return jsonify({"error": "Feedback must be 'Satisfied' or 'Unsatisfied'"}), 400

    try:
        result = Result.query.filter_by(
            result_id=result_id,
            user_id=current_user.id,
        ).first()

        if not result:
            return jsonify({"error": "Result not found"}), 404

        if feedback == "Satisfied":
            result.feedback = result.prediction
        else:
            result.feedback = "Fake" if result.prediction == "Real" else "Real"

        db_session.commit()

        return (
            jsonify(
                {
                    "message": "Feedback saved successfully",
                    "result": result_to_dict(result),
                }
            ),
            200,
        )

    except IntegrityError:
        db_session.rollback()
        return (
            jsonify({"error": "Database integrity error while saving feedback."}),
            500,
        )
    except DatabaseError:
        db_session.rollback()
        return (
            jsonify({"error": "A database error occurred while saving feedback."}),
            500,
        )
    except Exception as e:
        db_session.rollback()
        return log_and_respond("Failed to save feedback.", e)


@app.route("/api/media/result/<int:result_id>/<string:media_kind>", methods=["GET"])
def api_result_media(result_id, media_kind):
    if not current_user.is_authenticated:
        return jsonify({"error": "Authentication required"}), 401

    if media_kind not in {"image", "gradcam"}:
        return jsonify({"error": "Media not found"}), 404

    try:
        result = Result.query.filter_by(
            result_id=result_id,
            user_id=current_user.id,
        ).first()

        if not result:
            return jsonify({"error": "Result not found"}), 404

        media_path = result.image_path if media_kind == "image" else result.gradcam_path
        if not media_path:
            return jsonify({"error": "Media not found"}), 404

        return send_media_path(media_path)

    except NotFound:
        return jsonify({"error": "Media not found"}), 404
    except Exception as e:
        return log_and_respond("Failed to load protected media.", e)


@app.route("/api/media/guest/<string:media_kind>", methods=["GET"])
def api_guest_media(media_kind):
    if media_kind not in {"image", "gradcam"}:
        return jsonify({"error": "Media not found"}), 404

    guest_result = session.get("guest_result")
    if not guest_result:
        return jsonify({"error": "Media not found"}), 404

    media_path = guest_result.get("image_path") if media_kind == "image" else guest_result.get("gradcam_path")
    if not media_path:
        return jsonify({"error": "Media not found"}), 404

    try:
        return send_media_path(media_path)
    except NotFound:
        return jsonify({"error": "Media not found"}), 404
    except Exception as e:
        return log_and_respond("Failed to load guest media.", e)


# Performance API
@app.route("/api/performance", methods=["GET"])
def api_performance():
    try:
        performances = Performance.query.all()

        if not performances:
            return (
                jsonify(
                    {
                        "error": "No performance data available.",
                        "models": [],
                    }
                ),
                404,
            )

        best_model = max(performances, key=lambda p: p.accuracy)

        return (
            jsonify(
                {
                    "bestModel": {
                        "id": best_model.id,
                        "modelName": best_model.model_name,
                        "accuracy": best_model.accuracy,
                        "precision": best_model.precision,
                        "recall": best_model.recall,
                        "f1Score": best_model.f1_score,
                        "aucRoc": best_model.auc_roc,
                        "prAuc": best_model.pr_auc,
                        "tp": best_model.tp,
                        "tn": best_model.tn,
                        "fp": best_model.fp,
                        "fn": best_model.fn,
                    },
                    "models": [performance_to_dict(p) for p in performances],
                }
            ),
            200,
        )

    except Exception as e:
        return log_and_respond("Failed to load performance data.", e)



if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}
    app.run(debug=debug)
