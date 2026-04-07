def test_auth_me_returns_not_authenticated_for_guest(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 200
    data = response.get_json()
    assert data["authenticated"] is False
    assert data["user"] is None


def test_register_creates_user_and_logs_them_in(client):
    response = client.post(
        "/api/auth/register",
        json={
            "username": "athar",
            "email": "athar@example.com",
            "password": "secret123",
            "confirmPassword": "secret123",
        },
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Registration successful"
    assert data["user"]["username"] == "athar"
    assert data["user"]["email"] == "athar@example.com"

    me_response = client.get("/api/auth/me")
    me_data = me_response.get_json()
    assert me_data["authenticated"] is True
    assert me_data["user"]["email"] == "athar@example.com"


def test_register_rejects_password_mismatch(client):
    response = client.post(
        "/api/auth/register",
        json={
            "username": "athar",
            "email": "athar@example.com",
            "password": "secret123",
            "confirmPassword": "wrong123",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Passwords do not match"


def test_login_succeeds_with_valid_credentials(client):
    client.post(
        "/api/auth/register",
        json={
            "username": "athar",
            "email": "athar@example.com",
            "password": "secret123",
            "confirmPassword": "secret123",
        },
    )

    client.post("/api/auth/logout")

    response = client.post(
        "/api/auth/login",
        json={
            "email": "athar@example.com",
            "password": "secret123",
        },
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Login successful"
    assert data["user"]["email"] == "athar@example.com"


def test_login_fails_with_invalid_password(client):
    client.post(
        "/api/auth/register",
        json={
            "username": "athar",
            "email": "athar@example.com",
            "password": "secret123",
            "confirmPassword": "secret123",
        },
    )

    client.post("/api/auth/logout")

    response = client.post(
        "/api/auth/login",
        json={
            "email": "athar@example.com",
            "password": "wrongpass",
        },
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid email or password"


def test_logout_clears_session(client):
    client.post(
        "/api/auth/register",
        json={
            "username": "athar",
            "email": "athar@example.com",
            "password": "secret123",
            "confirmPassword": "secret123",
        },
    )

    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200
    assert logout_response.get_json()["message"] == "Logged out successfully"

    me_response = client.get("/api/auth/me")
    me_data = me_response.get_json()
    assert me_data["authenticated"] is False
    assert me_data["user"] is None
