from pathlib import Path
import hashlib
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models"
MANIFEST = MODEL_DIR / "model_manifest.json"

if not MANIFEST.exists():
    raise SystemExit("ECHEC: model_manifest.json introuvable")
manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
records = {row["name"]: row for row in manifest["files"]}

errors = []
for name, row in records.items():
    path = MODEL_DIR / name
    if not path.exists():
        errors.append(f"manquant: {name}")
        continue
    if path.stat().st_size != row["size_bytes"]:
        errors.append(f"taille: {name}")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if sha != row["sha256"]:
        errors.append(f"sha256: {name}")

for fold in range(1, 6):
    mean = np.load(MODEL_DIR / f"outer{fold}_mean.npy", allow_pickle=False)
    std = np.load(MODEL_DIR / f"outer{fold}_std.npy", allow_pickle=False)
    if mean.shape != (1, 1, 12) or std.shape != (1, 1, 12):
        errors.append(f"shape scaler fold {fold}")
    if not np.isfinite(mean).all() or not np.isfinite(std).all() or not (std > 0).all():
        errors.append(f"contenu scaler fold {fold}")

if errors:
    print("BUNDLE INVALIDE")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print("BUNDLE VALIDE")
print("Version:", manifest["version"])
print("Task:", manifest["task"])
print("Threshold:", manifest["threshold"])
print("Files:", len(manifest["files"]))
