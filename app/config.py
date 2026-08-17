import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _path_from_env(name: str, default: Path) -> Path:
    raw = os.getenv(name)
    path = Path(raw) if raw else default
    if not path.is_absolute():
        path = BASE_DIR / path
    return path.resolve()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")

    database_url = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'cardioai.db'}")
    # Render supplies PostgreSQL URLs as postgresql://... while this project
    # intentionally installs psycopg v3 (psycopg[binary]). Force the
    # SQLAlchemy psycopg3 dialect explicitly to avoid a psycopg2 import error.
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", "8")) * 1024 * 1024
    WTF_CSRF_TIME_LIMIT = None

    MODEL_DIR = _path_from_env("MODEL_DIR", BASE_DIR / "models")
    MODEL_THRESHOLD = float(os.getenv("MODEL_THRESHOLD", "0.72"))
    MODEL_VERSION = os.getenv("MODEL_VERSION", "raw-inceptiontime-se-nested-v1")
    DEMO_MODE = _bool("DEMO_MODE", False)
    ENABLE_XAI = _bool("ENABLE_XAI", True)
    AUTO_INIT_DB = _bool("AUTO_INIT_DB", True)
    AUTO_CREATE_ADMIN = _bool("AUTO_CREATE_ADMIN", True)

    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip().lower()
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
    API_KEY = os.getenv("API_KEY", "")

    TARGET_FS = int(os.getenv("TARGET_FS", "100"))
    TARGET_LENGTH = int(os.getenv("TARGET_LENGTH", "1000"))
    LEADS = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]

    VALIDATION_DATA_PATH = BASE_DIR / "app" / "data" / "deployment_pipeline_validation.json"
    SAMPLE_DATA_DIR = BASE_DIR / "sample_data" / "public_demo"

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool("SESSION_COOKIE_SECURE", False)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    PUBLIC_DEMO_NOTICE = (
    "CardioAI Assist — plateforme Data & IA fonctionnelle et déployée pour l’analyse assistée d’ECG 12 dérivations, "
    "intégrant validation patient-wise, validation externe, explicabilité et traçabilité. "
    "Les résultats sont destinés à l’évaluation méthodologique et à l’aide à l’analyse ; "
    "ils ne remplacent pas un diagnostic médical."
)
