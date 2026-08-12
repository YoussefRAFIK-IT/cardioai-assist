from __future__ import annotations

import hashlib
import io
import json
from dataclasses import dataclass
from math import gcd
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import resample_poly


LEADS = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]


def _norm_lead(value: str) -> str:
    return str(value).strip().lower().replace(" ", "").replace("-", "").replace("_", "")


@dataclass
class ParsedECG:
    raw_signal: np.ndarray
    windows: np.ndarray
    sampling_rate_original: int
    sampling_rate_target: int
    duration_seconds: float
    warnings: list[str]
    quality: dict
    sha256: str
    original_filename: str


def _interpolate_missing(x: np.ndarray, warnings: list[str]) -> tuple[np.ndarray, float]:
    x = x.astype(np.float32, copy=True)
    missing_fraction = float(np.isnan(x).mean())
    if missing_fraction == 0:
        return x, 0.0
    if missing_fraction > 0.10:
        raise ValueError(
            f"Le signal contient {missing_fraction:.1%} de valeurs manquantes, au-delà de la limite technique de 10 %."
        )
    warnings.append(f"{missing_fraction:.2%} de valeurs manquantes ont été interpolées.")
    for j in range(x.shape[1]):
        s = pd.Series(x[:, j])
        x[:, j] = s.interpolate(limit_direction="both").fillna(0.0).to_numpy(dtype=np.float32)
    return x, missing_fraction


def _validate_shape(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x)
    if x.ndim != 2:
        raise ValueError(f"Le signal doit être une matrice 2D. Forme reçue : {x.shape}.")
    if x.shape[1] == 12:
        return x.astype(np.float32)
    if x.shape[0] == 12:
        return x.T.astype(np.float32)
    raise ValueError(f"Le fichier doit contenir exactement 12 dérivations. Forme reçue : {x.shape}.")


def _from_csv(data: bytes) -> np.ndarray:
    df = pd.read_csv(io.BytesIO(data))
    normalized_columns = {_norm_lead(c): c for c in df.columns}

    if all(_norm_lead(lead) in normalized_columns for lead in LEADS):
        ordered = [normalized_columns[_norm_lead(lead)] for lead in LEADS]
        return df[ordered].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float32)

    # To avoid silent lead-order errors, CSV/TXT files must name the 12 leads.
    raise ValueError(
        "Le CSV/TXT doit contenir les 12 colonnes nommées I, II, III, aVR, aVL, aVF, V1, V2, V3, V4, V5, V6. "
        "Une colonne temporelle supplémentaire est autorisée."
    )


def _from_json(data: bytes) -> tuple[np.ndarray, int | None]:
    obj = json.loads(data.decode("utf-8"))
    fs = None
    if isinstance(obj, dict):
        fs = obj.get("sampling_rate") or obj.get("fs")
        if "leads" in obj and isinstance(obj["leads"], dict):
            columns = []
            lead_map = {_norm_lead(k): v for k, v in obj["leads"].items()}
            for lead in LEADS:
                key = _norm_lead(lead)
                if key not in lead_map:
                    raise ValueError(f"Dérivation manquante dans le JSON : {lead}")
                columns.append(np.asarray(lead_map[key], dtype=np.float32))
            lengths = {len(c) for c in columns}
            if len(lengths) != 1:
                raise ValueError("Toutes les dérivations JSON doivent avoir la même longueur.")
            return np.column_stack(columns), int(fs) if fs else None
        if "signal" in obj:
            return np.asarray(obj["signal"], dtype=np.float32), int(fs) if fs else None
    raise ValueError(
        "JSON invalide. Utilisez un objet contenant 'sampling_rate' et un dictionnaire 'leads' avec les 12 dérivations."
    )


def _resample(x: np.ndarray, fs_original: int, fs_target: int, warnings: list[str]) -> np.ndarray:
    if fs_original <= 0:
        raise ValueError("La fréquence d'échantillonnage doit être positive.")
    if fs_original == fs_target:
        return x.astype(np.float32)
    factor = gcd(fs_original, fs_target)
    up, down = fs_target // factor, fs_original // factor
    y = resample_poly(x, up=up, down=down, axis=0).astype(np.float32)
    warnings.append(f"Signal rééchantillonné de {fs_original} Hz vers {fs_target} Hz.")
    return y


def _make_windows(x: np.ndarray, target_len: int, warnings: list[str]) -> np.ndarray:
    n = len(x)
    if n < target_len:
        raise ValueError(
            f"Signal trop court après rééchantillonnage : {n} points. "
            f"Le pipeline validé exige au minimum {target_len} points (10 s à 100 Hz)."
        )
    if n == target_len:
        return x[None, ...].astype(np.float32)

    max_start = n - target_len
    starts = sorted(set([
        0,
        int(round(max_start * 0.25)),
        int(round(max_start * 0.50)),
        int(round(max_start * 0.75)),
        max_start,
    ]))
    windows = np.stack([x[start:start + target_len] for start in starts]).astype(np.float32)
    warnings.append(
        f"Signal long : {len(starts)} fenêtres de 10 s ont été analysées aux positions début, 25 %, centre, 75 % et fin."
    )
    return windows


def parse_upload(file_storage, sampling_rate: int, target_fs: int = 100, target_len: int = 1000) -> ParsedECG:
    if not file_storage or not file_storage.filename:
        raise ValueError("Aucun fichier n'a été fourni.")

    filename = Path(file_storage.filename).name
    data = file_storage.read()
    if not data:
        raise ValueError("Le fichier est vide.")

    digest = hashlib.sha256(data).hexdigest()
    suffix = Path(filename).suffix.lower()
    fs_from_file = None
    warnings: list[str] = []

    if suffix in {".csv", ".txt"}:
        x = _from_csv(data)
    elif suffix == ".npy":
        x = np.load(io.BytesIO(data), allow_pickle=False)
        warnings.append(
            "Format NPY : l'application suppose explicitement l'ordre standard des 12 dérivations documenté dans le projet."
        )
    elif suffix == ".json":
        x, fs_from_file = _from_json(data)
    else:
        raise ValueError("Format non pris en charge. Utilisez CSV, JSON ou NPY.")

    x = _validate_shape(x)
    x, missing_fraction = _interpolate_missing(x, warnings)

    if not np.isfinite(x).all():
        raise ValueError("Le signal contient des valeurs infinies non valides.")

    lead_std = np.std(x, axis=0)
    flat_leads = [LEADS[j] for j in range(12) if float(lead_std[j]) < 1e-8]
    if flat_leads:
        warnings.append("Dérivations presque constantes détectées : " + ", ".join(flat_leads))

    fs_original = int(fs_from_file or sampling_rate)
    if fs_original < 25 or fs_original > 5000:
        raise ValueError(f"Fréquence d'échantillonnage incohérente : {fs_original} Hz.")

    duration = float(len(x) / fs_original)
    x_resampled = _resample(x, fs_original, target_fs, warnings)
    windows = _make_windows(x_resampled, target_len, warnings)

    quality = {
        "missing_fraction": missing_fraction,
        "flat_leads": flat_leads,
        "max_abs_amplitude": float(np.max(np.abs(x_resampled))),
        "mean_abs_amplitude": float(np.mean(np.abs(x_resampled))),
        "minimum_lead_std": float(np.std(x_resampled, axis=0).min()),
        "maximum_lead_std": float(np.std(x_resampled, axis=0).max()),
        "points_after_resampling": int(len(x_resampled)),
        "segment_count": int(len(windows)),
    }

    return ParsedECG(
        raw_signal=x_resampled,
        windows=windows,
        sampling_rate_original=fs_original,
        sampling_rate_target=target_fs,
        duration_seconds=duration,
        warnings=warnings,
        quality=quality,
        sha256=digest,
        original_filename=filename,
    )


def make_preview(signal: np.ndarray, points: int = 250) -> dict:
    signal = np.asarray(signal, dtype=np.float32)
    indices = np.linspace(0, len(signal) - 1, min(points, len(signal))).astype(int)
    sampled = signal[indices]
    return {
        "leads": LEADS,
        "time_index": indices.tolist(),
        "values": sampled.round(6).tolist(),
    }
