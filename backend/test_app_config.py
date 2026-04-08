import os

import pytest

from app import create_app


def test_create_app_requires_secret_key(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="SECRET_KEY must be set"):
        create_app()


def test_create_app_uses_secret_key_from_environment(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "configured-test-secret")

    app = create_app()

    assert app.secret_key == "configured-test-secret"
