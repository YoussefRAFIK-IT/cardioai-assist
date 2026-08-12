from __future__ import annotations

import numpy as np
from .ecg_parser import LEADS


def compute_occlusion(predictor, window: np.ndarray, temporal_step: int = 100, temporal_width: int = 100):
    """Occlusion simple. Positive importance = la probabilité baisse après masquage."""
    baseline = predictor.predict(window[None, ...]).probability

    lead_importance = []
    for j, lead in enumerate(LEADS):
        occluded = window.copy()
        occluded[:, j] = float(np.mean(window[:, j]))
        p = predictor.predict(occluded[None, ...]).probability
        lead_importance.append({"lead": lead, "importance": float(baseline - p), "abs_importance": float(abs(baseline - p))})
    lead_importance.sort(key=lambda x: x["abs_importance"], reverse=True)

    temporal_importance = []
    for start in range(0, len(window) - temporal_width + 1, temporal_step):
        end = start + temporal_width
        occluded = window.copy()
        occluded[start:end, :] = np.mean(window[start:end, :], axis=0, keepdims=True)
        p = predictor.predict(occluded[None, ...]).probability
        temporal_importance.append({
            "start_seconds": start / 100.0,
            "end_seconds": end / 100.0,
            "importance": float(baseline - p),
            "abs_importance": float(abs(baseline - p)),
        })
    temporal_importance.sort(key=lambda x: x["abs_importance"], reverse=True)

    return {
        "baseline_probability": baseline,
        "lead_importance": lead_importance,
        "temporal_importance": temporal_importance,
        "warning": "Explication exploratoire de sensibilité du modèle, sans validation clinique individuelle.",
    }
