from __future__ import annotations

from functools import wraps

from flask import Blueprint, current_app, jsonify, request

from ..extensions import csrf
from ..services.ecg_parser import parse_upload
from ..services.inference import get_predictor

bp = Blueprint("api", __name__, url_prefix="/api/v1")
csrf.exempt(bp)


def api_key_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        configured = current_app.config.get("API_KEY", "")
        if not configured:
            return jsonify({"error": "API désactivée : configurez API_KEY."}), 503
        if request.headers.get("X-API-Key") != configured:
            return jsonify({"error": "Clé API invalide."}), 401
        return fn(*args, **kwargs)
    return wrapper


@bp.get("/health")
def health():
    predictor = get_predictor(current_app.config)
    status = predictor.status()
    if not status["demo_mode_configured"] and not status["real_bundle_ready"]:
        return jsonify({"status": "degraded", "model": status}), 503
    return jsonify({"status": "ok", "model": status})


@bp.post("/predict")
@api_key_required
def predict_api():
    try:
        sampling_rate = int(request.form.get("sampling_rate", "100"))
        parsed = parse_upload(
            request.files.get("ecg_file"),
            sampling_rate=sampling_rate,
            target_fs=current_app.config["TARGET_FS"],
            target_len=current_app.config["TARGET_LENGTH"],
        )
        output = get_predictor(current_app.config).predict(parsed.windows)
        return jsonify({
            "probability": output.probability,
            "threshold": output.threshold,
            "predicted_class": output.predicted_class,
            "predicted_label": "MI" if output.predicted_class else "NORM",
            "mode": output.inference_mode,
            "model_version": output.model_version,
            "model_count": output.model_count,
            "bundle_fingerprint": output.bundle_fingerprint,
            "latency_ms": output.latency_ms,
            "segments": len(parsed.windows),
            "quality": parsed.quality,
            "warnings": parsed.warnings,
            "notice": current_app.config["PUBLIC_DEMO_NOTICE"],
        })
    except Exception as exc:
        current_app.logger.exception("API prediction failed")
        return jsonify({"error": str(exc)}), 400

@bp.post("/warmup")
@api_key_required
def warmup_api():
    """Load and compile the real model ensemble after deployment."""
    try:
        predictor = get_predictor(current_app.config)
        result = predictor.warmup()
        return jsonify(result)
    except Exception as exc:
        current_app.logger.exception("Model warm-up failed")
        return jsonify({"error": str(exc)}), 503

