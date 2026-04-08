import io
import os

from PIL import Image

import routes
from app import db
from test_models import Result


def register_and_login(client, username="athar", email="athar@example.com", password="secret123"):
    return client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "confirmPassword": password,
        },
    )


def fetch_csrf_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    return response.get_json()["csrfToken"]


def write_media_file(app, relative_path: str, content: bytes = b"media-bytes"):
    absolute_path = os.path.join(app.static_folder, relative_path.replace("/", os.sep))
    directory = os.path.dirname(absolute_path)
    os.makedirs(directory, exist_ok=True)
    with open(absolute_path, "wb") as file_handle:
        file_handle.write(content)


def make_test_image(filename="face.jpg", image_format="JPEG"):
    image_bytes = io.BytesIO()
    Image.new("RGB", (64, 64), color=(120, 180, 200)).save(image_bytes, format=image_format)
    image_bytes.seek(0)
    return image_bytes, filename


def test_results_requires_authentication(client):
    response = client.get("/api/results")

    assert response.status_code == 401
    assert response.get_json()["error"] == "Authentication required"


def test_results_returns_only_logged_in_users_results(client):
    register_and_login(client)

    with client.application.app_context():
        user_id = 1

        db.session.add_all([
            Result(
                confidence_score=97.5,
                prediction="Fake",
                feedback=None,
                image_path="uploads/fake1.jpg",
                gradcam_path="gradcam/fake1.jpg",
                explanation="Fake explanation",
                recommendation="Review carefully",
                inference_time=0.9,
                user_id=user_id,
            ),
            Result(
                confidence_score=88.2,
                prediction="Real",
                feedback=None,
                image_path="uploads/real1.jpg",
                gradcam_path="gradcam/real1.jpg",
                explanation="Real explanation",
                recommendation="Looks authentic",
                inference_time=0.8,
                user_id=user_id,
            ),
        ])
        db.session.commit()

    response = client.get("/api/results")

    assert response.status_code == 200
    data = response.get_json()
    assert len(data["results"]) == 2
    assert {item["prediction"] for item in data["results"]} == {"Fake", "Real"}


def test_result_detail_returns_single_saved_result(client):
    register_and_login(client)

    with client.application.app_context():
        result = Result(
            confidence_score=91.4,
            prediction="Fake",
            feedback=None,
            image_path="uploads/test.jpg",
            gradcam_path="gradcam/test.jpg",
            explanation="Model detected suspicious artifacts",
            recommendation="Treat with caution",
            inference_time=1.1,
            user_id=1,
        )
        db.session.add(result)
        db.session.commit()
        result_id = result.result_id

    response = client.get(f"/api/results/{result_id}")

    assert response.status_code == 200
    data = response.get_json()
    assert data["result"]["id"] == result_id
    assert data["result"]["prediction"] == "Fake"
    assert data["result"]["imagePath"] == "uploads/test.jpg"


def test_result_detail_returns_404_for_missing_result(client):
    register_and_login(client)

    response = client.get("/api/results/999")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Result not found"


def test_feedback_requires_authentication(client):
    response = client.post(
        "/api/results/1/feedback",
        json={"feedback": "Satisfied"},
        headers={"X-CSRF-Token": fetch_csrf_token(client)},
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "Authentication required"


def test_feedback_updates_result_for_satisfied(client):
    register_and_login(client)
    csrf_token = fetch_csrf_token(client)

    with client.application.app_context():
        result = Result(
            confidence_score=93.0,
            prediction="Fake",
            feedback=None,
            image_path="uploads/fake.jpg",
            gradcam_path="gradcam/fake.jpg",
            explanation="Explanation",
            recommendation="Recommendation",
            inference_time=1.0,
            user_id=1,
        )
        db.session.add(result)
        db.session.commit()
        result_id = result.result_id

    response = client.post(
        f"/api/results/{result_id}/feedback",
        json={"feedback": "Satisfied"},
        headers={"X-CSRF-Token": csrf_token},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Feedback saved successfully"
    assert data["result"]["feedback"] == "Fake"


def test_feedback_updates_result_for_unsatisfied(client):
    register_and_login(client)
    csrf_token = fetch_csrf_token(client)

    with client.application.app_context():
        result = Result(
            confidence_score=84.0,
            prediction="Real",
            feedback=None,
            image_path="uploads/real.jpg",
            gradcam_path="gradcam/real.jpg",
            explanation="Explanation",
            recommendation="Recommendation",
            inference_time=1.0,
            user_id=1,
        )
        db.session.add(result)
        db.session.commit()
        result_id = result.result_id

    response = client.post(
        f"/api/results/{result_id}/feedback",
        json={"feedback": "Unsatisfied"},
        headers={"X-CSRF-Token": csrf_token},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["result"]["feedback"] == "Fake"


def test_feedback_rejects_invalid_value(client):
    register_and_login(client)
    csrf_token = fetch_csrf_token(client)

    with client.application.app_context():
        result = Result(
            confidence_score=84.0,
            prediction="Real",
            feedback=None,
            image_path="uploads/real.jpg",
            gradcam_path="gradcam/real.jpg",
            explanation="Explanation",
            recommendation="Recommendation",
            inference_time=1.0,
            user_id=1,
        )
        db.session.add(result)
        db.session.commit()
        result_id = result.result_id

    response = client.post(
        f"/api/results/{result_id}/feedback",
        json={"feedback": "Maybe"},
        headers={"X-CSRF-Token": csrf_token},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Feedback must be 'Satisfied' or 'Unsatisfied'"


def test_feedback_requires_csrf_token(client):
    register_and_login(client)

    with client.application.app_context():
        result = Result(
            confidence_score=84.0,
            prediction="Real",
            feedback=None,
            image_path="uploads/real.jpg",
            gradcam_path="gradcam/real.jpg",
            explanation="Explanation",
            recommendation="Recommendation",
            inference_time=1.0,
            user_id=1,
        )
        db.session.add(result)
        db.session.commit()
        result_id = result.result_id

    response = client.post(
        f"/api/results/{result_id}/feedback",
        json={"feedback": "Satisfied"},
    )

    assert response.status_code == 403
    assert response.get_json()["error"] == "Invalid CSRF token"


def test_result_media_requires_authentication(client):
    response = client.get("/api/media/result/1/image")

    assert response.status_code == 401
    assert response.get_json()["error"] == "Authentication required"


def test_result_media_serves_only_owner_files(client):
    register_and_login(client)

    with client.application.app_context():
        result = Result(
            confidence_score=91.4,
            prediction="Fake",
            feedback=None,
            image_path="uploads/protected.jpg",
            gradcam_path="gradcam/protected.jpg",
            explanation="Model detected suspicious artifacts",
            recommendation="Treat with caution",
            inference_time=1.1,
            user_id=1,
        )
        db.session.add(result)
        db.session.commit()
        result_id = result.result_id

    write_media_file(client.application, "uploads/protected.jpg", b"protected-image")

    response = client.get(f"/api/media/result/{result_id}/image")

    assert response.status_code == 200
    assert response.data == b"protected-image"


def test_result_media_blocks_other_users(client):
    register_and_login(client, username="owner", email="owner@example.com")

    with client.application.app_context():
        result = Result(
            confidence_score=91.4,
            prediction="Fake",
            feedback=None,
            image_path="uploads/private.jpg",
            gradcam_path="gradcam/private.jpg",
            explanation="Model detected suspicious artifacts",
            recommendation="Treat with caution",
            inference_time=1.1,
            user_id=1,
        )
        db.session.add(result)
        db.session.commit()
        result_id = result.result_id

    owner_csrf = fetch_csrf_token(client)
    client.post("/api/auth/logout", headers={"X-CSRF-Token": owner_csrf})
    register_and_login(client, username="other", email="other@example.com")

    response = client.get(f"/api/media/result/{result_id}/image")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Result not found"


def test_guest_media_serves_latest_guest_upload(client, monkeypatch):
    monkeypatch.setattr(routes, "filter_image", lambda _filepath: True)
    monkeypatch.setattr(
        routes,
        "predict_image",
        lambda _filepath: {
            "prediction": "Fake",
            "confidence": 99.1,
            "gradcam_path": "gradcam/test_gradcam.jpg",
            "explanation": "Mock explanation",
            "recommendation": "Mock recommendation",
            "inference_time": 0.25,
        },
    )

    write_media_file(client.application, "gradcam/test_gradcam.jpg", b"guest-gradcam")

    upload_response = client.post(
        "/api/upload",
        data={
            "file": make_test_image()
        },
        content_type="multipart/form-data",
        headers={"X-CSRF-Token": fetch_csrf_token(client)},
    )

    assert upload_response.status_code == 200

    image_response = client.get("/api/media/guest/image")
    gradcam_response = client.get("/api/media/guest/gradcam")

    assert image_response.status_code == 200
    assert gradcam_response.status_code == 200
    assert gradcam_response.data == b"guest-gradcam"
