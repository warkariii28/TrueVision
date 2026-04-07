import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["GLOG_minloglevel"] = "3"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.session_protection = "strong"


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({
        "error": "Authentication required"
    }), 401


def env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if not value:
        return default

    return [item.strip() for item in value.split(",") if item.strip()]


def create_app():
    app = Flask(__name__, static_url_path="/static", static_folder="static")
    app_env = os.getenv("APP_ENV", os.getenv("FLASK_ENV", "development")).lower()
    is_production = app_env == "production"
    secret_key = os.getenv("SECRET_KEY")

    if is_production and not secret_key:
        raise RuntimeError("SECRET_KEY must be set when APP_ENV=production")

    cors_origins = env_list(
        "CORS_ORIGINS",
        [
            "http://localhost:4200",
            "http://127.0.0.1:4200",
        ],
    )

    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
    app.config["SESSION_COOKIE_SECURE"] = env_flag(
        "SESSION_COOKIE_SECURE",
        is_production,
    )
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = os.getenv(
        "SESSION_COOKIE_SAMESITE",
        "Lax",
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "database.db"),
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = "static/uploads"
    app.config["GRADCAM_FOLDER"] = "static/gradcam"
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

    app.secret_key = secret_key or "dev-secret-key"

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    CORS(
        app,
        supports_credentials=True,
        resources={
            r"/api/*": {
                "origins": cors_origins
            }
        },
    )

    if env_flag("PRELOAD_MODEL", False):
        from inference import preload_model
        preload_model()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
