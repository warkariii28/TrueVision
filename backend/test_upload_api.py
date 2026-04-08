import io

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


def make_test_image(filename="face.jpg", image_format="JPEG"):
    image_bytes = io.BytesIO()
    Image.new("RGB", (64, 64), color=(120, 180, 200)).save(image_bytes, format=image_format)
    image_bytes.seek(0)
    return image_bytes, filename


def fetch_csrf_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    return response.get_json()["csrfToken"]


def test_upload_requires_file_in_request(client):
    response = client.post(
        "/api/upload",
        data={},
        content_type="multipart/form-data",
        headers={"X-CSRF-Token": fetch_csrf_token(client)},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "No file was included in the request"


def test_upload_rejects_unsupported_file_type(client):
    response = client.post(
        "/api/upload",
        data={
            "file": (io.BytesIO(b"fake file contents"), "test.gif"),
        },
        content_type="multipart/form-data",
        headers={"X-CSRF-Token": fetch_csrf_token(client)},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Unsupported file type. Please upload a PNG, JPG, or JPEG image."


def test_upload_rejects_empty_filename(client):
    response = client.post(
        "/api/upload",
        data={
            "file": (io.BytesIO(b""), ""),
        },
        content_type="multipart/form-data",
        headers={"X-CSRF-Token": fetch_csrf_token(client)},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "No file was selected"


def test_guest_upload_returns_unsaved_result(client, monkeypatch):
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

    response = client.post(
        "/api/upload",
        data={
            "file": make_test_image(),
        },
        content_type="multipart/form-data",
        headers={"X-CSRF-Token": fetch_csrf_token(client)},
    )

    assert response.status_code == 200
    data = response.get_json()

    assert data["message"] == "Upload processed successfully"
    assert data["result"]["saved"] is False
    assert data["result"]["id"] is None
    assert data["result"]["prediction"] == "Fake"
    assert data["result"]["confidence"] == 99.1
    assert data["result"]["imagePath"] is None
    assert data["result"]["gradcamPath"] is None


def test_authenticated_upload_saves_result(client, monkeypatch):
    register_response = register_and_login(client)
    csrf_token = register_response.get_json()["csrfToken"]

    monkeypatch.setattr(routes, "filter_image", lambda _filepath: True)
    monkeypatch.setattr(
        routes,
        "predict_image",
        lambda _filepath: {
            "prediction": "Real",
            "confidence": 87.4,
            "gradcam_path": "gradcam/test_gradcam.jpg",
            "explanation": "Mock explanation",
            "recommendation": "Mock recommendation",
            "inference_time": 0.33,
        },
    )

    response = client.post(
        "/api/upload",
        data={
            "file": make_test_image(),
        },
        content_type="multipart/form-data",
        headers={"X-CSRF-Token": csrf_token},
    )

    assert response.status_code == 201
    data = response.get_json()

    assert data["message"] == "Upload processed successfully"
    assert data["result"]["saved"] is True
    assert data["result"]["prediction"] == "Real"
    assert data["result"]["confidence"] == 87.4

    with client.application.app_context():
        saved_results = Result.query.all()
        assert len(saved_results) == 1
        assert saved_results[0].prediction == "Real"


def test_upload_rejects_blurry_or_invalid_image(client, monkeypatch):
    monkeypatch.setattr(routes, "filter_image", lambda _filepath: False)

    response = client.post(
        "/api/upload",
        data={
            "file": make_test_image(),
        },
        content_type="multipart/form-data",
        headers={"X-CSRF-Token": fetch_csrf_token(client)},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "The image was too unclear to analyze. Please use a sharper, well-lit face image."
    )


def test_upload_returns_error_when_prediction_fails(client, monkeypatch):
    monkeypatch.setattr(routes, "filter_image", lambda _filepath: True)
    monkeypatch.setattr(
        routes,
        "predict_image",
        lambda _filepath: {"error": "Model inference failed"},
    )

    response = client.post(
        "/api/upload",
        data={
            "file": make_test_image(),
        },
        content_type="multipart/form-data",
        headers={"X-CSRF-Token": fetch_csrf_token(client)},
    )

    assert response.status_code == 500
    assert response.get_json()["error"] == "Model inference failed"


def test_upload_rejects_invalid_image_content(client):
    response = client.post(
        "/api/upload",
        data={
            "file": (io.BytesIO(b"not a real image"), "face.jpg"),
        },
        content_type="multipart/form-data",
        headers={"X-CSRF-Token": fetch_csrf_token(client)},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "The uploaded file is not a valid PNG or JPEG image."


def test_upload_is_rate_limited(client, monkeypatch):
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

    csrf_token = fetch_csrf_token(client)

    for _ in range(8):
        response = client.post(
            "/api/upload",
            data={
                "file": make_test_image(),
            },
            content_type="multipart/form-data",
            headers={"X-CSRF-Token": csrf_token},
        )
        assert response.status_code == 200

    limited_response = client.post(
        "/api/upload",
        data={
            "file": make_test_image(),
        },
        content_type="multipart/form-data",
        headers={"X-CSRF-Token": csrf_token},
    )

    assert limited_response.status_code == 429
    assert limited_response.headers["Retry-After"]
    assert limited_response.get_json()["error"] == "Too many requests. Please wait before trying again."


def test_upload_requires_csrf_token(client):
    response = client.post(
        "/api/upload",
        data={
            "file": make_test_image(),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 403
    assert response.get_json()["error"] == "Invalid CSRF token"
