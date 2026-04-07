from datetime import datetime

from flask_login import UserMixin

from app import db


class User(UserMixin, db.Model):
    __tablename__ = "user"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pwd = db.Column(db.String(300), nullable=False)


class Result(db.Model):
    __tablename__ = "result"
    __table_args__ = {"extend_existing": True}

    result_id = db.Column(db.Integer, primary_key=True)
    confidence_score = db.Column(db.Float, nullable=False)
    prediction = db.Column(db.String(10), nullable=False)
    feedback = db.Column(db.String(200), nullable=True)
    image_path = db.Column(db.String(255), nullable=False)
    gradcam_path = db.Column(db.String(255), nullable=True)
    explanation = db.Column(db.Text, nullable=True)
    recommendation = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    inference_time = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class Performance(db.Model):
    __tablename__ = "performance"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(50))
    accuracy = db.Column(db.Float)
    precision = db.Column(db.Float)
    recall = db.Column(db.Float)
    f1_score = db.Column(db.Float)
    fpr = db.Column(db.Float)
    fnr = db.Column(db.Float)
    tnr = db.Column(db.Float)
    tp = db.Column(db.Integer)
    tn = db.Column(db.Integer)
    fp = db.Column(db.Integer)
    fn = db.Column(db.Integer)
    auc_roc = db.Column(db.Float)
    pr_auc = db.Column(db.Float)
    confusion_matrix = db.Column(db.Text, nullable=True)


def predict_image(_filepath):
    return {
        "prediction": "Fake",
        "confidence": 99.0,
        "gradcam_path": "gradcam/test.jpg",
        "explanation": "Test explanation",
        "recommendation": "Test recommendation",
        "inference_time": 0.1,
    }
