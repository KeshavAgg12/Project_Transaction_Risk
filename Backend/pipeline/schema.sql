-- PostgreSQL schema for the fraud-risk pipeline. Safe to re-run.

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id          TEXT PRIMARY KEY,
    timestamp               TIMESTAMPTZ NOT NULL,
    customer_id             TEXT NOT NULL,
    amount                  NUMERIC(12, 2) NOT NULL,
    currency                TEXT NOT NULL DEFAULT 'INR',
    merchant_category       TEXT NOT NULL,
    distance_from_home_km   DOUBLE PRECISION NOT NULL,
    transactions_last_hour  INTEGER NOT NULL,
    hour_of_day             SMALLINT NOT NULL CHECK (hour_of_day BETWEEN 0 AND 23),
    payment_method          TEXT NOT NULL,
    is_fraud                SMALLINT,
    risk_score              SMALLINT NOT NULL CHECK (risk_score BETWEEN 0 AND 100),
    level                   TEXT NOT NULL CHECK (level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    decision                TEXT NOT NULL CHECK (decision IN ('Approved', 'Review', 'Blocked')),
    reasons                 JSONB NOT NULL DEFAULT '[]'::jsonb,
    contributions           JSONB,
    model_version           TEXT NOT NULL,
    source                  TEXT NOT NULL CHECK (source IN ('synthetic', 'manual')),
    alert_status            TEXT CHECK (alert_status IN ('open', 'investigating', 'resolved')),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_transactions_timestamp    ON transactions (timestamp);
CREATE INDEX IF NOT EXISTS idx_transactions_level        ON transactions (level);
CREATE INDEX IF NOT EXISTS idx_transactions_decision     ON transactions (decision);
CREATE INDEX IF NOT EXISTS idx_transactions_source       ON transactions (source);
CREATE INDEX IF NOT EXISTS idx_transactions_alert_status ON transactions (alert_status);
CREATE INDEX IF NOT EXISTS idx_transactions_customer_id  ON transactions (customer_id);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id         TEXT PRIMARY KEY,
    started_at     TIMESTAMPTZ NOT NULL,
    finished_at    TIMESTAMPTZ,
    status         TEXT NOT NULL,
    total_rows     INTEGER,
    summary        JSONB,
    model_version  TEXT
);

CREATE TABLE IF NOT EXISTS stage_runs (
    id           BIGSERIAL PRIMARY KEY,
    run_id       TEXT NOT NULL REFERENCES pipeline_runs (run_id) ON DELETE CASCADE,
    stage_name   TEXT NOT NULL,
    started_at   TIMESTAMPTZ NOT NULL,
    finished_at  TIMESTAMPTZ,
    duration_ms  INTEGER,
    rows_in      INTEGER,
    rows_out     INTEGER,
    error_count  INTEGER NOT NULL DEFAULT 0,
    status       TEXT NOT NULL,
    message      TEXT
);

CREATE INDEX IF NOT EXISTS idx_stage_runs_run_id ON stage_runs (run_id);

CREATE TABLE IF NOT EXISTS model_versions (
    version              TEXT PRIMARY KEY,
    model_type           TEXT NOT NULL,
    trained_at           TIMESTAMPTZ NOT NULL,
    metrics              JSONB,
    feature_importances  JSONB,
    is_active            BOOLEAN NOT NULL DEFAULT FALSE
);
