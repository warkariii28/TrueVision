import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
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
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    headers_enabled=True,
)


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


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value.strip())
    except ValueError:
        return default


def env_rate_limit(count_name: str, window_name: str, default_count: int, default_window: int) -> str:
    count = env_int(count_name, default_count)
    window_seconds = env_int(window_name, default_window)
    unit = "second" if window_seconds == 1 else "seconds"
    return f"{count} per {window_seconds} {unit}"


def create_app():
    app = Flask(__name__, static_url_path="/static", static_folder="static")
    app_env = os.getenv("APP_ENV", os.getenv("FLASK_ENV", "development")).lower()
    is_production = app_env == "production"
    secret_key = (os.getenv("SECRET_KEY") or "").strip()

    if not secret_key:
        raise RuntimeError("SECRET_KEY must be set")

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
    app.config["UPLOAD_FOLDER"] = os.path.join(app.static_folder, "uploads")
    app.config["GRADCAM_FOLDER"] = os.path.join(app.static_folder, "gradcam")
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
    app.config["LOGIN_RATE_LIMIT"] = env_rate_limit(
        "LOGIN_RATE_LIMIT_COUNT",
        "LOGIN_RATE_LIMIT_WINDOW",
        10,
        300,
    )
    app.config["REGISTER_RATE_LIMIT"] = env_rate_limit(
        "REGISTER_RATE_LIMIT_COUNT",
        "REGISTER_RATE_LIMIT_WINDOW",
        5,
        600,
    )
    app.config["UPLOAD_RATE_LIMIT"] = env_rate_limit(
        "UPLOAD_RATE_LIMIT_COUNT",
        "UPLOAD_RATE_LIMIT_WINDOW",
        8,
        600,
    )
    app.config["RATELIMIT_ENABLED"] = env_flag("RATELIMIT_ENABLED", True)
    app.config["RATELIMIT_HEADERS_ENABLED"] = True
    app.config["RATELIMIT_STORAGE_URI"] = os.getenv(
        "RATELIMIT_STORAGE_URI",
        os.getenv("REDIS_URL", "memory://"),
    )

    app.secret_key = secret_key

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)

    @app.errorhandler(429)
    def handle_rate_limit(error):
        response = jsonify({"error": "Too many requests. Please wait before trying again."})
        response.status_code = 429

        if hasattr(error, "get_response"):
            original_response = error.get_response()
            for header, value in original_response.headers.items():
                header_name = header.lower()
                if header_name == "retry-after" or header_name.startswith("x-ratelimit-"):
                    response.headers[header] = value

        return response

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
    debug = env_flag("FLASK_DEBUG", False)
    app.run(debug=debug)
