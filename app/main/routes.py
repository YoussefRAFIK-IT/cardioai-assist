from __future__ import annotations

import json
import uuid
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
from flask import Blueprint, Response, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from plotly.subplots import make_subplots
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models import ECGRecord, Explanation, Prediction
from ..services.ecg_parser import LEADS, make_preview, parse_upload
from ..services.explainability import compute_occlusion
from ..services.inference import get_predictor
from ..services.pdf_report import build_prediction_pdf
from ..utils import audit

bp = Blueprint("main", __name__)


def _preview_plot(preview: dict) -> str:
    values = np.asarray(preview["values"], dtype=float)
    t = np.asarray(preview["time_index"], dtype=float) / 100.0
    fig = make_subplots(rows=12, cols=1, shared_xaxes=True, vertical_spacing=0.008, subplot_titles=preview["leads"])
    for i, lead in enumerate(preview["leads"]):
        fig.add_trace(go.Scatter(x=t, y=values[:, i], mode="lines", name=lead, line={"width": 1}), row=i + 1, col=1)
    fig.update_layout(height=1100, showlegend=False, margin={"l": 50, "r": 20, "t": 30, "b": 40}, template="plotly_white")
    fig.update_xaxes(title_text="Temps (s)", row=12, col=1)
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True, "displaylogo": False})


def _load_validation_summary() -> dict:
    path = Path(current_app.config["VALIDATION_DATA_PATH"])
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@bp.route("/dashboard")
@login_required
def dashboard():
    predictor = get_predictor(current_app.config)
    total = Prediction.query.count()
    positives = Prediction.query.filter_by(predicted_class=1).count()
    avg_prob = db.session.query(db.func.avg(Prediction.probability)).scalar() or 0.0
    recent = Prediction.query.order_by(Prediction.created_at.desc()).limit(8).all()
    return render_template(
        "dashboard.html",
        total=total,
        positives=positives,
        avg_prob=float(avg_prob),
        recent=recent,
        model_status=predictor.status(),
    )


@bp.route("/model-validation")
@login_required
def model_validation():
    return render_template(
        "model_validation.html",
        validation=_load_validation_summary(),
        model_status=get_predictor(current_app.config).status(),
    )


@bp.route("/sample/<path:filename>")
@login_required
def sample_file(filename: str):
    allowed = {
        "ptbdb_demo_healthy_correct.csv",
        "ptbdb_demo_healthy_correct.json",
        "ptbdb_demo_mi_correct.csv",
        "ptbdb_demo_mi_correct.json",
        "ptbdb_demo_borderline_correct.csv",
        "ptbdb_demo_borderline_correct.json",
    }
    if filename not in allowed:
        return ("Fichier non autorisé", 404)
    directory = Path(current_app.config["SAMPLE_DATA_DIR"])
    return send_from_directory(directory, filename, as_attachment=True)


@bp.route("/analyze", methods=["GET", "POST"])
@login_required
def analyze():
    samples = [
        ("Contrôle sain externe correctement classé", "ptbdb_demo_healthy_correct.csv"),
        ("MI externe correctement classé", "ptbdb_demo_mi_correct.csv"),
        ("Cas externe proche du seuil", "ptbdb_demo_borderline_correct.csv"),
    ]
    if request.method == "GET":
        return render_template("analyze.html", leads=LEADS, samples=samples)

    try:
        sampling_rate = int(request.form.get("sampling_rate", "100"))
        parsed = parse_upload(
            request.files.get("ecg_file"),
            sampling_rate=sampling_rate,
            target_fs=current_app.config["TARGET_FS"],
            target_len=current_app.config["TARGET_LENGTH"],
        )
        predictor = get_predictor(current_app.config)
        output = predictor.predict(parsed.windows)

        ref = str(uuid.uuid4())
        record = ECGRecord(
            public_ref=ref,
            original_filename=secure_filename(parsed.original_filename),
            file_sha256=parsed.sha256,
            source="web_upload",
            sampling_rate=parsed.sampling_rate_original,
            duration_seconds=parsed.duration_seconds,
            lead_count=12,
            segment_count=len(parsed.windows),
            preview_json=json.dumps(make_preview(parsed.windows[0]), ensure_ascii=False),
            warnings_json=json.dumps(parsed.warnings, ensure_ascii=False),
        )
        db.session.add(record)
        db.session.flush()

        prediction = Prediction(
            ecg_id=record.id,
            user_id=current_user.id,
            model_version=output.model_version,
            inference_mode=output.inference_mode,
            probability=output.probability,
            threshold=output.threshold,
            predicted_class=output.predicted_class,
            latency_ms=output.latency_ms,
            details_json=json.dumps({
                "per_window": output.per_window,
                "per_model": output.per_model,
                "model_count": output.model_count,
                "bundle_fingerprint": output.bundle_fingerprint,
                "quality": parsed.quality,
            }, ensure_ascii=False),
        )
        db.session.add(prediction)
        db.session.flush()

        if request.form.get("compute_xai") == "yes" and current_app.config["ENABLE_XAI"]:
            xai = compute_occlusion(predictor, parsed.windows[0])
            explanation = Explanation(
                prediction_id=prediction.id,
                method="lead_and_temporal_occlusion",
                lead_importance_json=json.dumps(xai["lead_importance"], ensure_ascii=False),
                temporal_importance_json=json.dumps(xai["temporal_importance"], ensure_ascii=False),
            )
            db.session.add(explanation)

        db.session.commit()
        audit("prediction_created", "prediction", prediction.id, {
            "mode": output.inference_mode,
            "model_version": output.model_version,
            "segments": len(parsed.windows),
        })
        return redirect(url_for("main.result", prediction_id=prediction.id))

    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("ECG analysis failed")
        flash(str(exc), "danger")
        return render_template("analyze.html", leads=LEADS, samples=samples), 400


@bp.route("/result/<int:prediction_id>")
@login_required
def result(prediction_id: int):
    prediction = Prediction.query.get_or_404(prediction_id)
    if prediction.user_id != current_user.id and current_user.role != "admin":
        return ("Accès refusé", 403)
    preview = json.loads(prediction.ecg_record.preview_json or "{}")
    plot_html = _preview_plot(preview) if preview else None
    warnings = json.loads(prediction.ecg_record.warnings_json or "[]")
    lead_importance, temporal_importance = [], []
    if prediction.explanation:
        lead_importance = json.loads(prediction.explanation.lead_importance_json or "[]")
        temporal_importance = json.loads(prediction.explanation.temporal_importance_json or "[]")
    details = json.loads(prediction.details_json or "{}")
    return render_template(
        "result.html",
        prediction=prediction,
        plot_html=plot_html,
        warnings=warnings,
        lead_importance=lead_importance,
        temporal_importance=temporal_importance,
        details=details,
    )


@bp.route("/history")
@login_required
def history():
    page = max(int(request.args.get("page", 1)), 1)
    query = Prediction.query
    if current_user.role != "admin":
        query = query.filter_by(user_id=current_user.id)
    pagination = query.order_by(Prediction.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template("history.html", pagination=pagination)


@bp.route("/report/<int:prediction_id>.pdf")
@login_required
def report_pdf(prediction_id: int):
    prediction = Prediction.query.get_or_404(prediction_id)
    if prediction.user_id != current_user.id and current_user.role != "admin":
        return ("Accès refusé", 403)
    content = build_prediction_pdf(prediction, current_app.config["PUBLIC_DEMO_NOTICE"])
    return Response(
        content,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=cardioai_{prediction.ecg_record.public_ref}.pdf"},
    )
