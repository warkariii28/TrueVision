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
    response = client.post("/api/results/1/feedback", json={"feedback": "Satisfied"})

    assert response.status_code == 401
    assert response.get_json()["error"] == "Authentication required"


def test_feedback_updates_result_for_satisfied(client):
    register_and_login(client)

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
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Feedback saved successfully"
    assert data["result"]["feedback"] == "Fake"


def test_feedback_updates_result_for_unsatisfied(client):
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
        json={"feedback": "Unsatisfied"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["result"]["feedback"] == "Fake"


def test_feedback_rejects_invalid_value(client):
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
        json={"feedback": "Maybe"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Feedback must be 'Satisfied' or 'Unsatisfied'"
