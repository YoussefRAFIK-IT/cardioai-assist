from functools import wraps

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import AuditLog, ECGRecord, ModelVersion, Prediction, User
from ..services.inference import get_predictor
from ..utils import audit

bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role != "admin":
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


@bp.get("/")
@admin_required
def index():
    predictor = get_predictor(current_app.config)
    return render_template(
        "admin.html",
        users=User.query.order_by(User.created_at.desc()).all(),
        model_versions=ModelVersion.query.order_by(ModelVersion.created_at.desc()).all(),
        audits=AuditLog.query.order_by(AuditLog.created_at.desc()).limit(20).all(),
        model_status=predictor.status(),
        stats={
            "users": User.query.count(),
            "ecg_records": ECGRecord.query.count(),
            "predictions": Prediction.query.count(),
            "audit_logs": AuditLog.query.count(),
        },
    )


@bp.post("/users/create")
@admin_required
def create_user():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    role = request.form.get("role", "analyst")
    if role not in {"analyst", "admin"}:
        role = "analyst"
    if not email or "@" not in email:
        flash("Adresse e-mail invalide.", "danger")
        return redirect(url_for("admin.index"))
    if len(password) < 12:
        flash("Le mot de passe doit contenir au moins 12 caractères.", "danger")
        return redirect(url_for("admin.index"))
    if User.query.filter_by(email=email).first():
        flash("Cet utilisateur existe déjà.", "warning")
        return redirect(url_for("admin.index"))
    user = User(email=email, role=role, active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    audit("admin_user_created", "user", user.id, {"role": role})
    flash("Utilisateur créé.", "success")
    return redirect(url_for("admin.index"))


@bp.post("/users/<int:user_id>/toggle")
@admin_required
def toggle_user(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if user.id == current_user.id:
        flash("Vous ne pouvez pas désactiver votre propre compte.", "warning")
        return redirect(url_for("admin.index"))
    user.active = not user.active
    db.session.commit()
    audit("admin_user_toggled", "user", user.id, {"active": user.active})
    flash("Statut utilisateur mis à jour.", "success")
    return redirect(url_for("admin.index"))
