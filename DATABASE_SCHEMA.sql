CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'analyst',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE model_versions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    version VARCHAR(120) UNIQUE NOT NULL,
    threshold DOUBLE PRECISION NOT NULL,
    mode VARCHAR(40) NOT NULL,
    metrics_json TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE ecg_records (
    id SERIAL PRIMARY KEY,
    public_ref VARCHAR(36) UNIQUE NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_sha256 VARCHAR(64) NOT NULL,
    source VARCHAR(80) NOT NULL,
    sampling_rate INTEGER NOT NULL,
    duration_seconds DOUBLE PRECISION NOT NULL,
    lead_count INTEGER NOT NULL DEFAULT 12,
    segment_count INTEGER NOT NULL DEFAULT 1,
    preview_json TEXT,
    warnings_json TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    ecg_id INTEGER NOT NULL REFERENCES ecg_records(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    model_version VARCHAR(120) NOT NULL,
    inference_mode VARCHAR(40) NOT NULL,
    probability DOUBLE PRECISION NOT NULL CHECK (probability >= 0 AND probability <= 1),
    threshold DOUBLE PRECISION NOT NULL,
    predicted_class INTEGER NOT NULL CHECK (predicted_class IN (0,1)),
    latency_ms DOUBLE PRECISION NOT NULL,
    details_json TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE explanations (
    id SERIAL PRIMARY KEY,
    prediction_id INTEGER UNIQUE NOT NULL REFERENCES predictions(id) ON DELETE CASCADE,
    method VARCHAR(80) NOT NULL,
    lead_importance_json TEXT,
    temporal_importance_json TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(120) NOT NULL,
    resource_type VARCHAR(80),
    resource_id VARCHAR(80),
    ip_hash VARCHAR(64),
    details_json TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_predictions_created_at ON predictions(created_at DESC);
CREATE INDEX idx_ecg_records_hash ON ecg_records(file_sha256);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);

CREATE INDEX idx_predictions_user_created ON predictions(user_id, created_at DESC);
