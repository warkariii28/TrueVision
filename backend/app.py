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


def create_app():
    app = Flask(__name__, static_url_path="/static", static_folder="static")

    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
    app.config["SESSION_COOKIE_SECURE"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "database.db"),
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = "static/uploads"
    app.config["GRADCAM_FOLDER"] = "static/gradcam"
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    CORS(
        app,
        supports_credentials=True,
        resources={
            r"/api/*": {
                "origins": [
                    "http://localhost:4200",
                    "http://127.0.0.1:4200",
                ]
            }
        },
    )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
