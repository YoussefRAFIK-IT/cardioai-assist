from flask import Flask, render_template
from .config import Config
from .extensions import csrf, db, login_manager
from .models import ModelVersion, User


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def _initialize_database(app):
    with app.app_context():
        db.create_all()
        version = app.config["MODEL_VERSION"]
        if not ModelVersion.query.filter_by(version=version).first():
            db.session.add(ModelVersion(
                name="RAW InceptionTime-SE 5-fold ensemble",
                version=version,
                threshold=app.config["MODEL_THRESHOLD"],
                mode="DEMO" if app.config["DEMO_MODE"] else "REAL",
                metrics_json=(
                    '{"internal_oof_roc_auc":0.9777939,"internal_oof_pr_auc":0.9669649,'
                    '"external_patient_roc_auc":0.9460759,"external_patient_pr_auc":0.9823804,'
                    '"external_locked_threshold_sensitivity":0.5405405,'
                    '"external_locked_threshold_specificity":1.0}'
                ),
            ))
        if app.config["AUTO_CREATE_ADMIN"]:
            email = app.config["ADMIN_EMAIL"].strip().lower()
            password = app.config["ADMIN_PASSWORD"]
            if email and password and not User.query.filter_by(email=email).first():
                user = User(email=email, role="admin", active=True)
                user.set_password(password)
                db.session.add(user)
        db.session.commit()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .auth.routes import bp as auth_bp
    from .main.routes import bp as main_bp
    from .api.routes import bp as api_bp
    from .admin.routes import bp as admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)

    @app.context_processor
    def inject_notice():
        return {"public_demo_notice": app.config["PUBLIC_DEMO_NOTICE"]}

    @app.errorhandler(403)
    def forbidden(_):
        return render_template("error.html", title="Accès refusé", message="Vous n'avez pas les droits nécessaires."), 403

    @app.errorhandler(413)
    def too_large(_):
        return render_template("error.html", title="Fichier trop volumineux", message="Le fichier dépasse la taille autorisée."), 413

    @app.errorhandler(404)
    def not_found(_):
        return render_template("error.html", title="Page introuvable", message="La ressource demandée n'existe pas."), 404

    if app.config["AUTO_INIT_DB"]:
        _initialize_database(app)
    return app
