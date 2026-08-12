"""Run a real inference on the three external PTBDB public demo ECGs.
Requires TensorFlow and the application dependencies.
"""
from pathlib import Path
from types import SimpleNamespace

from app.services.ecg_parser import parse_upload
from app.services.inference import ECGPredictor

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "sample_data" / "public_demo"

class Upload:
    def __init__(self, path):
        self.path = Path(path)
        self.filename = self.path.name
    def read(self):
        return self.path.read_bytes()

predictor = ECGPredictor(
    model_dir=ROOT / "models",
    threshold=0.72,
    version="raw-inceptiontime-se-nested-v1",
    demo_mode=False,
)
print("Bundle:", predictor.status())
for name in [
    "ptbdb_demo_healthy_correct.csv",
    "ptbdb_demo_mi_correct.csv",
    "ptbdb_demo_borderline_correct.csv",
]:
    parsed = parse_upload(Upload(SAMPLES / name), sampling_rate=100)
    output = predictor.predict(parsed.windows)
    print(name, {
        "probability": round(output.probability, 6),
        "predicted_class": output.predicted_class,
        "mode": output.inference_mode,
        "segments": len(parsed.windows),
        "latency_ms": round(output.latency_ms, 1),
    })
