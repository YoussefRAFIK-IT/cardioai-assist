from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="analyst")
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    predictions = db.relationship("Prediction", back_populates="user", lazy="dynamic")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return bool(self.active)


class ModelVersion(db.Model):
    __tablename__ = "model_versions"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    version = db.Column(db.String(120), unique=True, nullable=False, index=True)
    threshold = db.Column(db.Float, nullable=False)
    mode = db.Column(db.String(40), nullable=False, default="REAL")
    metrics_json = db.Column(db.Text, nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class ECGRecord(db.Model):
    __tablename__ = "ecg_records"
    id = db.Column(db.Integer, primary_key=True)
    public_ref = db.Column(db.String(36), unique=True, nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    file_sha256 = db.Column(db.String(64), nullable=False, index=True)
    source = db.Column(db.String(80), nullable=False, default="upload")
    sampling_rate = db.Column(db.Integer, nullable=False)
    duration_seconds = db.Column(db.Float, nullable=False)
    lead_count = db.Column(db.Integer, nullable=False, default=12)
    segment_count = db.Column(db.Integer, nullable=False, default=1)
    preview_json = db.Column(db.Text, nullable=True)
    warnings_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    predictions = db.relationship("Prediction", back_populates="ecg_record", cascade="all, delete-orphan")


class Prediction(db.Model):
    __tablename__ = "predictions"
    id = db.Column(db.Integer, primary_key=True)
    ecg_id = db.Column(db.Integer, db.ForeignKey("ecg_records.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    model_version = db.Column(db.String(120), nullable=False)
    inference_mode = db.Column(db.String(40), nullable=False)
    probability = db.Column(db.Float, nullable=False)
    threshold = db.Column(db.Float, nullable=False)
    predicted_class = db.Column(db.Integer, nullable=False)
    latency_ms = db.Column(db.Float, nullable=False)
    details_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    ecg_record = db.relationship("ECGRecord", back_populates="predictions")
    user = db.relationship("User", back_populates="predictions")
    explanation = db.relationship("Explanation", back_populates="prediction", uselist=False, cascade="all, delete-orphan")


class Explanation(db.Model):
    __tablename__ = "explanations"
    id = db.Column(db.Integer, primary_key=True)
    prediction_id = db.Column(db.Integer, db.ForeignKey("predictions.id"), unique=True, nullable=False)
    method = db.Column(db.String(80), nullable=False)
    lead_importance_json = db.Column(db.Text, nullable=True)
    temporal_importance_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    prediction = db.relationship("Prediction", back_populates="explanation")


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    action = db.Column(db.String(120), nullable=False)
    resource_type = db.Column(db.String(80), nullable=True)
    resource_id = db.Column(db.String(80), nullable=True)
    ip_hash = db.Column(db.String(64), nullable=True)
    details_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
