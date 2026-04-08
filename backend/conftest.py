import os
import sys
import types

import pytest


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["FLASK_DEBUG"] = "false"
os.environ["RATELIMIT_STORAGE_URI"] = "memory://"

fake_models = types.ModuleType("models")
fake_inference = types.ModuleType("inference")

from test_models import Performance, Result, User, predict_image

fake_models.User = User
fake_models.Result = Result
fake_models.Performance = Performance
fake_inference.predict_image = predict_image

sys.modules["models"] = fake_models
sys.modules["inference"] = fake_inference

import routes
from app import db, limiter


@pytest.fixture
def client():
    app = routes.app
    app.config["TESTING"] = True
    limiter.reset()

    with app.app_context():
        db.drop_all()
        db.create_all()

    with app.test_client() as test_client:
        yield test_client

    with app.app_context():
        db.session.remove()
        db.drop_all()
    limiter.reset()
