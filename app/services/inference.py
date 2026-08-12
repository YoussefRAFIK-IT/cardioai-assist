from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np


EXPECTED_LEADS = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
EXPECTED_INPUT_SHAPE = [1000, 12]
EXPECTED_PARAMETER_COUNT = 502_497
EXPECTED_MODEL_COUNT = 5


@dataclass
class PredictionOutput:
    probability: float
    threshold: float
    predicted_class: int
    inference_mode: str
    model_version: str
    latency_ms: float
    per_window: list[float]
    per_model: list[float]
    model_count: int
    bundle_fingerprint: str | None


class ECGPredictor:
    """Predictor for the validated five-fold RAW InceptionTime-SE deployment pipeline.

    Important safety rule: when DEMO_MODE is false, a missing or invalid real bundle
    raises a blocking error. There is no silent fallback to synthetic inference.
    """

    def __init__(self, model_dir: Path, threshold: float, version: str, demo_mode: bool = False):
        self.model_dir = Path(model_dir)
        self.threshold = float(threshold)
        self.version = str(version)
        self.demo_mode = bool(demo_mode)
        self._models = None
        self._means = None
        self._stds = None
        self._manifest = None
        self._validation = None
        self._lock = threading.Lock()

    @property
    def manifest_path(self) -> Path:
        return self.model_dir / "model_manifest.json"

    @property
    def expected_files(self) -> list[Path]:
        files = []
        for fold in range(1, EXPECTED_MODEL_COUNT + 1):
            files.extend([
                self.model_dir / f"nested_gpu_inceptiontime_se_outer{fold}.keras",
                self.model_dir / f"outer{fold}_mean.npy",
                self.model_dir / f"outer{fold}_std.npy",
            ])
        return files

    def _read_manifest(self) -> dict:
        if not self.manifest_path.exists():
            raise RuntimeError(f"Manifeste du modèle introuvable : {self.manifest_path}")
        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError("Le manifeste du modèle est illisible ou invalide.") from exc
        return manifest

    def validate_bundle(self, force: bool = False) -> dict:
        if self._validation is not None and not force:
            return self._validation

        errors: list[str] = []
        details: list[dict] = []
        manifest = None
        fingerprint = None

        try:
            manifest = self._read_manifest()
            fingerprint = hashlib.sha256(self.manifest_path.read_bytes()).hexdigest()[:16]

            if manifest.get("version") != self.version:
                errors.append(
                    f"Version manifeste={manifest.get('version')} différente de MODEL_VERSION={self.version}."
                )
            if manifest.get("task") != "MI_vs_strict_NORM":
                errors.append("La tâche du manifeste n'est pas MI_vs_strict_NORM.")
            if manifest.get("input_shape") != EXPECTED_INPUT_SHAPE:
                errors.append(f"Input shape du manifeste invalide : {manifest.get('input_shape')}.")
            if int(manifest.get("sampling_rate_hz", -1)) != 100:
                errors.append("La fréquence attendue du manifeste doit être 100 Hz.")
            if manifest.get("leads") != EXPECTED_LEADS:
                errors.append("L'ordre des 12 dérivations dans le manifeste est invalide.")
            manifest_threshold = float(manifest.get("threshold", -1))
            if abs(manifest_threshold - self.threshold) > 1e-12:
                errors.append(
                    f"Seuil du manifeste ({manifest_threshold}) différent du seuil configuré ({self.threshold})."
                )

            records = {row.get("name"): row for row in manifest.get("files", [])}
            expected_names = {p.name for p in self.expected_files}
            if set(records) != expected_names:
                missing = sorted(expected_names - set(records))
                extra = sorted(set(records) - expected_names)
                if missing:
                    errors.append("Fichiers absents du manifeste : " + ", ".join(missing))
                if extra:
                    errors.append("Fichiers inattendus dans le manifeste : " + ", ".join(extra))

            for path in self.expected_files:
                row = records.get(path.name, {})
                exists = path.exists()
                sha_ok = False
                size_ok = False
                if exists:
                    actual_size = path.stat().st_size
                    actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
                    size_ok = actual_size == row.get("size_bytes")
                    sha_ok = actual_sha == row.get("sha256")
                details.append({
                    "file": path.name,
                    "exists": exists,
                    "size_ok": size_ok,
                    "sha256_ok": sha_ok,
                })
                if not exists:
                    errors.append(f"Fichier modèle/scaler manquant : {path.name}")
                elif not size_ok:
                    errors.append(f"Taille inattendue : {path.name}")
                elif not sha_ok:
                    errors.append(f"Empreinte SHA-256 invalide : {path.name}")

            # Validate scaler contents without TensorFlow.
            for fold in range(1, EXPECTED_MODEL_COUNT + 1):
                mean_path = self.model_dir / f"outer{fold}_mean.npy"
                std_path = self.model_dir / f"outer{fold}_std.npy"
                if mean_path.exists() and std_path.exists():
                    try:
                        mean = np.load(mean_path, allow_pickle=False)
                        std = np.load(std_path, allow_pickle=False)
                        if mean.shape != (1, 1, 12):
                            errors.append(f"Shape mean fold {fold} invalide : {mean.shape}")
                        if std.shape != (1, 1, 12):
                            errors.append(f"Shape std fold {fold} invalide : {std.shape}")
                        if not np.isfinite(mean).all() or not np.isfinite(std).all():
                            errors.append(f"NaN/Inf dans les scalers du fold {fold}.")
                        if not (std > 0).all():
                            errors.append(f"Écart-type non positif dans le fold {fold}.")
                    except Exception as exc:
                        errors.append(f"Scaler fold {fold} illisible : {exc}")

        except Exception as exc:
            errors.append(str(exc))

        self._manifest = manifest
        self._validation = {
            "valid": not errors,
            "errors": errors,
            "files": details,
            "manifest_fingerprint": fingerprint,
        }
        return self._validation

    def real_bundle_ready(self) -> bool:
        return bool(self.validate_bundle().get("valid"))

    def status(self) -> dict:
        validation = self.validate_bundle()
        configured_mode = "DEMO_SYNTHETIC" if self.demo_mode else "REAL_RAW_ENSEMBLE"
        return {
            "configured_mode": configured_mode,
            "demo_mode_configured": self.demo_mode,
            "real_bundle_ready": bool(validation["valid"]),
            "bundle_errors": validation["errors"],
            "model_dir": str(self.model_dir),
            "threshold": self.threshold,
            "version": self.version,
            "model_count": EXPECTED_MODEL_COUNT,
            "manifest_fingerprint": validation.get("manifest_fingerprint"),
        }

    def _load_real_bundle(self):
        if self._models is not None:
            return
        with self._lock:
            if self._models is not None:
                return

            validation = self.validate_bundle(force=True)
            if not validation["valid"]:
                raise RuntimeError(
                    "Le bundle réel est invalide. L'inférence est bloquée : "
                    + " | ".join(validation["errors"])
                )

            try:
                import tensorflow as tf
            except Exception as exc:
                raise RuntimeError("TensorFlow n'est pas installé ou ne peut pas être chargé.") from exc

            models, means, stds = [], [], []
            for fold in range(1, EXPECTED_MODEL_COUNT + 1):
                model_path = self.model_dir / f"nested_gpu_inceptiontime_se_outer{fold}.keras"
                mean_path = self.model_dir / f"outer{fold}_mean.npy"
                std_path = self.model_dir / f"outer{fold}_std.npy"

                model = tf.keras.models.load_model(model_path, compile=False)
                if tuple(model.input_shape[-2:]) != (1000, 12):
                    raise RuntimeError(f"Input shape invalide pour le modèle fold {fold}: {model.input_shape}")
                if model.output_shape[-1] != 1:
                    raise RuntimeError(f"Output shape invalide pour le modèle fold {fold}: {model.output_shape}")
                if int(model.count_params()) != EXPECTED_PARAMETER_COUNT:
                    raise RuntimeError(
                        f"Nombre de paramètres inattendu fold {fold}: {model.count_params()} "
                        f"(attendu {EXPECTED_PARAMETER_COUNT})"
                    )

                models.append(model)
                means.append(np.load(mean_path, allow_pickle=False).astype(np.float32))
                stds.append(np.load(std_path, allow_pickle=False).astype(np.float32))

            self._models, self._means, self._stds = models, means, stds

    @staticmethod
    def _demo_probability(windows: np.ndarray) -> tuple[float, list[float], list[float]]:
        """Deterministic UI-only synthetic score. Never used when DEMO_MODE=false."""
        probs = []
        for window in windows:
            std = float(np.mean(np.std(window, axis=0)))
            diff = float(np.mean(np.abs(np.diff(window, axis=0))))
            energy = float(np.mean(np.square(window)))
            score = -0.8 + 1.8 * np.tanh(std) + 2.2 * np.tanh(diff * 5.0) + 0.7 * np.tanh(energy)
            probs.append(float(1.0 / (1.0 + np.exp(-score))))
        return float(np.mean(probs)), probs, [float(np.mean(probs))]

    def _real_probability(self, windows: np.ndarray) -> tuple[float, list[float], list[float]]:
        self._load_real_bundle()

        # Exact deployment pipeline validated on PTBDB:
        # each fold model receives all windows normalized with its own scaler;
        # probabilities are averaged across models, then across windows.
        model_by_window = []
        for model, mean, std in zip(self._models, self._means, self._stds):
            normalized = (windows.astype(np.float32) - mean) / (std + 1e-8)
            probabilities = model.predict(normalized, batch_size=min(64, len(windows)), verbose=0).reshape(-1)
            model_by_window.append(probabilities.astype(float))

        matrix = np.stack(model_by_window, axis=0)  # (5, n_windows)
        per_window = matrix.mean(axis=0).tolist()
        per_model = matrix.mean(axis=1).tolist()
        probability = float(matrix.mean())
        return probability, [float(x) for x in per_window], [float(x) for x in per_model]

    def warmup(self) -> dict:
        """Load the real bundle and compile one inference pass without storing a result.

        This is intended for controlled post-deploy warm-up so the first jury-facing
        request does not pay the TensorFlow cold-start cost.
        """
        if self.demo_mode:
            return {
                "mode": "DEMO_SYNTHETIC",
                "warmed": False,
                "message": "Warm-up réel ignoré car DEMO_MODE=true.",
            }

        if not self.real_bundle_ready():
            errors = self.validate_bundle().get("errors", [])
            raise RuntimeError(
                "Warm-up impossible : bundle réel invalide. " + " | ".join(errors)
            )

        start = time.perf_counter()
        self._load_real_bundle()

        # One zero-valued technical tensor compiles the prediction path.
        # It is never stored, displayed, or interpreted as a medical result.
        technical_input = np.zeros((1, 1000, 12), dtype=np.float32)
        probability, _, _ = self._real_probability(technical_input)

        return {
            "mode": "REAL_RAW_ENSEMBLE",
            "warmed": True,
            "model_count": EXPECTED_MODEL_COUNT,
            "elapsed_ms": (time.perf_counter() - start) * 1000.0,
            "technical_probability_discarded": float(probability),
            "message": (
                "Warm-up technique terminé. La probabilité calculée sur un tenseur nul "
                "a été jetée et n'a aucune signification clinique."
            ),
        }


    def predict(self, windows: np.ndarray) -> PredictionOutput:
        windows = np.asarray(windows, dtype=np.float32)
        if windows.ndim != 3 or windows.shape[1:] != (1000, 12):
            raise ValueError(f"Forme attendue : (segments, 1000, 12), reçue : {windows.shape}")
        if not np.isfinite(windows).all():
            raise ValueError("Le signal contient des NaN ou Inf après prétraitement.")

        start = time.perf_counter()
        if self.demo_mode:
            probability, per_window, per_model = self._demo_probability(windows)
            mode = "DEMO_SYNTHETIC"
            fingerprint = None
            model_count = 0
        else:
            # No silent fallback: real mode must have a valid bundle.
            if not self.real_bundle_ready():
                errors = self.validate_bundle().get("errors", [])
                raise RuntimeError(
                    "Mode réel demandé mais bundle invalide. " + " | ".join(errors)
                )
            probability, per_window, per_model = self._real_probability(windows)
            mode = "REAL_RAW_ENSEMBLE"
            fingerprint = self.validate_bundle().get("manifest_fingerprint")
            model_count = EXPECTED_MODEL_COUNT

        latency = (time.perf_counter() - start) * 1000.0
        return PredictionOutput(
            probability=probability,
            threshold=self.threshold,
            predicted_class=int(probability >= self.threshold),
            inference_mode=mode,
            model_version=self.version,
            latency_ms=latency,
            per_window=per_window,
            per_model=per_model,
            model_count=model_count,
            bundle_fingerprint=fingerprint,
        )


_predictor = None


def get_predictor(config) -> ECGPredictor:
    global _predictor
    if _predictor is None:
        _predictor = ECGPredictor(
            model_dir=config["MODEL_DIR"],
            threshold=config["MODEL_THRESHOLD"],
            version=config["MODEL_VERSION"],
            demo_mode=config["DEMO_MODE"],
        )
    return _predictor
