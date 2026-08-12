from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from . import __init__  # noqa: F401
from ..extensions import db
from ..models import User
from ..utils import audit

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password) and user.active:
            login_user(user, remember=True)
            audit("login_success", "user", user.id)
            return redirect(request.args.get("next") or url_for("main.dashboard"))
        flash("Identifiants invalides.", "danger")
    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
def logout():
    if current_user.is_authenticated:
        audit("logout", "user", current_user.id)
    logout_user()
    return redirect(url_for("auth.login"))
