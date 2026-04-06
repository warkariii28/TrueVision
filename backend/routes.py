import os
import traceback
from datetime import timedelta
from uuid import uuid4

from flask import jsonify, request, session
from flask_login import current_user, login_user, logout_user
from sqlalchemy import func
from sqlalchemy.exc import (
    DataError,
    DatabaseError,
    IntegrityError,
    InterfaceError,
    InvalidRequestError,
)
from werkzeug.utils import secure_filename

from app import bcrypt, create_app, db, login_manager
from filter_utils import filter_image
from models import Performance, Result, User, predict_image


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


app = create_app()


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


def allowed_file(filename):
    if "." not in filename:
        return False

    name, ext = os.path.splitext(filename)

    if ext.lower().replace(".", "") not in ALLOWED_EXTENSIONS:
        return False

    if len(name) < 1:
        return False

    return True


# Auth APIs
@app.route("/api/auth/me", methods=["GET"])
def api_auth_me():
    if current_user.is_authenticated:
        return (
            jsonify(
                {
                    "authenticated": True,
                    "user": user_to_dict(current_user),
                }
            ),
            200,
        )

    return (
        jsonify(
            {
                "authenticated": False,
                "user": None,
            }
        ),
        200,
    )


@app.route("/api/auth/register", methods=["POST"])
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

        new_user = User(
            username=username,
            email=email,
            pwd=hashed_password,
        )

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        session.permanent = True

        return (
            jsonify(
                {
                    "message": "Registration successful",
                    "user": user_to_dict(new_user),
                }
            ),
            201,
        )

    except IntegrityError:
        db.session.rollback()
        return (
            jsonify(
                {
                    "error": "User already exists! Please use a different email or username."
                }
            ),
            409,
        )
    except DataError:
        db.session.rollback()
        return jsonify({"error": "Invalid entry"}), 400
    except InterfaceError:
        db.session.rollback()
        return jsonify({"error": "Database connection error"}), 500
    except DatabaseError:
        db.session.rollback()
        return jsonify({"error": "Database error"}), 500
    except InvalidRequestError:
        db.session.rollback()
        return jsonify({"error": "Something went wrong"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/auth/login", methods=["POST"])
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

            return (
                jsonify(
                    {
                        "message": "Login successful",
                        "user": user_to_dict(user),
                    }
                ),
                200,
            )

        return jsonify({"error": "Invalid email or password"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/auth/logout", methods=["POST"])
def api_auth_logout():
    if current_user.is_authenticated:
        logout_user()

    session.clear()

    return jsonify({"message": "Logged out successfully"}), 200


# Upload API
@app.route("/api/upload", methods=["POST"])
def api_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file was included in the request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file was selected"}), 400

    if not allowed_file(file.filename):
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
        original_filename = secure_filename(file.filename)
        ext = original_filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid4().hex}.{ext}"

        upload_dir = app.config["UPLOAD_FOLDER"]
        gradcam_dir = app.config["GRADCAM_FOLDER"]
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(gradcam_dir, exist_ok=True)

        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)

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
            new_result = Result(
                confidence_score=result["confidence"],
                prediction=result["prediction"],
                feedback=None,
                image_path=image_path,
                user_id=current_user.id,
                explanation=result.get("explanation", ""),
                gradcam_path=gradcam_rel_path,
                recommendation=result.get("recommendation", ""),
                inference_time=result.get("inference_time"),
            )

            db.session.add(new_result)
            db.session.commit()

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
            "id": None,
            "saved": False,
            "prediction": result["prediction"],
            "confidence": result["confidence"],
            "feedback": None,
            "imagePath": image_path,
            "gradcamPath": gradcam_rel_path,
            "explanation": result.get("explanation", ""),
            "recommendation": result.get("recommendation", ""),
            "createdAt": None,
            "inferenceTime": result.get("inference_time"),
        }

        return (
            jsonify(
                {
                    "message": "Upload processed successfully",
                    "result": guest_result,
                }
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()

        if filepath and os.path.exists(filepath):
            os.remove(filepath)

        app.logger.error(f"Error processing API upload: {str(e)}")
        app.logger.error(traceback.format_exc())

        return (
            jsonify(
                {"error": f"An error occurred while processing the upload: {str(e)}"}
            ),
            500,
        )


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
        return jsonify({"error": str(e)}), 500


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
        return jsonify({"error": str(e)}), 500


# Feedback API
@app.route("/api/results/<int:result_id>/feedback", methods=["POST"])
def api_submit_feedback(result_id):
    if not current_user.is_authenticated:
        return jsonify({"error": "Authentication required"}), 401

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

        db.session.commit()

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
        db.session.rollback()
        return (
            jsonify({"error": "Database integrity error while saving feedback."}),
            500,
        )
    except DatabaseError:
        db.session.rollback()
        return (
            jsonify({"error": "A database error occurred while saving feedback."}),
            500,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


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
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
