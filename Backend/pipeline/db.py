"""PostgreSQL layer: schema creation, idempotent bulk load, run logging, manual-transaction helpers."""
from __future__ import annotations

import argparse
import json
import logging
from contextlib import contextmanager
from typing import Any, Iterator

import numpy as np
import pandas as pd
from psycopg2.extras import execute_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

import config
import model as model_mod
import validate

log = logging.getLogger(__name__)

TXN_COLUMNS = [
    "transaction_id", "timestamp", "customer_id", "amount", "currency", "merchant_category",
    "distance_from_home_km", "transactions_last_hour", "hour_of_day", "payment_method", "is_fraud",
    "risk_score", "level", "decision", "reasons", "contributions", "model_version", "source", "alert_status",
]
JSON_COLUMNS = {"reasons", "contributions"}
LOAD_CHUNK = 10_000

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(config.database_url(), future=True)
    return _engine


@contextmanager
def raw_cursor() -> Iterator[Any]:
    conn = get_engine().raw_connection()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def create_schema() -> None:
    sql = config.SCHEMA_SQL.read_text()
    with get_engine().begin() as conn:
        conn.exec_driver_sql(sql)
    log.info("schema ready")


# --- Row preparation ---------------------------------------------------------
def _json(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, str):  # already serialised (e.g. read back from CSV)
        return value
    return json.dumps(value)


def _py(value: Any) -> Any:
    if value is None or (not isinstance(value, (list, dict, str)) and pd.isna(value)):
        return None
    return value.item() if isinstance(value, np.generic) else value


def with_alert_status(df: pd.DataFrame) -> pd.DataFrame:
    """alert_status = 'open' for every decision != Approved, otherwise NULL."""
    out = df.copy()
    out["alert_status"] = np.where(out["decision"] != config.APPROVED_DECISION, config.DEFAULT_ALERT_STATUS, None)
    return out


def _rows(df: pd.DataFrame) -> list[tuple]:
    rows = []
    for rec in df[TXN_COLUMNS].to_dict("records"):
        rows.append(tuple(_json(rec[c]) if c in JSON_COLUMNS else _py(rec[c]) for c in TXN_COLUMNS))
    return rows


UPSERT_SQL = f"""
INSERT INTO transactions ({", ".join(TXN_COLUMNS)}) VALUES %s
ON CONFLICT (transaction_id) DO UPDATE SET
    risk_score = EXCLUDED.risk_score, level = EXCLUDED.level, decision = EXCLUDED.decision,
    reasons = EXCLUDED.reasons, contributions = EXCLUDED.contributions,
    model_version = EXCLUDED.model_version, is_fraud = EXCLUDED.is_fraud,
    alert_status = CASE WHEN EXCLUDED.decision = '{config.APPROVED_DECISION}' THEN NULL
                        ELSE COALESCE(transactions.alert_status, EXCLUDED.alert_status) END
"""
TEMPLATE = "(" + ", ".join(
    f"%s::jsonb" if c in JSON_COLUMNS else "%s" for c in TXN_COLUMNS) + ")"


def load_transactions(df: pd.DataFrame) -> int:
    """Idempotent bulk upsert in chunks. Re-running with the same IDs updates, never duplicates.
    Existing alert_status (e.g. 'investigating') is preserved."""
    df = with_alert_status(df)
    rows = _rows(df)
    with raw_cursor() as cur:
        for i in range(0, len(rows), LOAD_CHUNK):
            execute_values(cur, UPSERT_SQL, rows[i:i + LOAD_CHUNK], template=TEMPLATE, page_size=LOAD_CHUNK)
    log.info("loaded %d transactions", len(rows))
    return len(rows)


def read_transactions(limit: int | None = None) -> pd.DataFrame:
    q = "SELECT * FROM transactions ORDER BY timestamp" + (f" LIMIT {int(limit)}" if limit else "")
    return pd.read_sql(text(q), get_engine())


def count_transactions() -> int:
    with get_engine().connect() as conn:
        return int(conn.execute(text("SELECT count(*) FROM transactions")).scalar_one())


# --- Run logging -----------------------------------------------------------------
def save_run(summary: dict[str, Any], stages: list[dict[str, Any]]) -> None:
    with raw_cursor() as cur:
        cur.execute(
            """INSERT INTO pipeline_runs (run_id, started_at, finished_at, status, total_rows, summary, model_version)
               VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)
               ON CONFLICT (run_id) DO UPDATE SET finished_at = EXCLUDED.finished_at, status = EXCLUDED.status,
                   total_rows = EXCLUDED.total_rows, summary = EXCLUDED.summary, model_version = EXCLUDED.model_version""",
            (summary["run_id"], summary["started_at"], summary["finished_at"], summary["status"],
             summary.get("total_rows"), json.dumps(summary), summary.get("model_version")))
        cur.execute("DELETE FROM stage_runs WHERE run_id = %s", (summary["run_id"],))
        for s in stages:
            cur.execute(
                """INSERT INTO stage_runs (run_id, stage_name, started_at, finished_at, duration_ms, rows_in,
                       rows_out, error_count, status, message) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (summary["run_id"], s["name"], s["started_at"], s["finished_at"], s["duration_ms"],
                 s["rows_in"], s["rows_out"], s["error_count"], s["status"], s["message"]))


def save_model_version(artifact: dict[str, Any], make_active: bool = True) -> None:
    with raw_cursor() as cur:
        if make_active:
            cur.execute("UPDATE model_versions SET is_active = FALSE")
        cur.execute(
            """INSERT INTO model_versions (version, model_type, trained_at, metrics, feature_importances, is_active)
               VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s)
               ON CONFLICT (version) DO UPDATE SET metrics = EXCLUDED.metrics,
                   feature_importances = EXCLUDED.feature_importances, is_active = EXCLUDED.is_active""",
            (artifact["version"], artifact["model_type"], artifact["trained_at"],
             json.dumps(artifact["metrics"]), json.dumps(artifact["feature_importances"]), make_active))


# --- Helpers for a future API ------------------------------------------------------
def _next_id(column: str, prefix: str, digits: int) -> str:
    q = text(f"SELECT max({column}) FROM transactions WHERE {column} LIKE :p")
    with get_engine().connect() as conn:
        current = conn.execute(q, {"p": f"{prefix}%"}).scalar_one()
    n = int(current[len(prefix):]) if current else 0
    return f"{prefix}{n + 1:0{digits}d}"


def next_manual_ids() -> dict[str, str]:
    """Next manual transaction_id (TXN-M000001...) and customer_id (CUST-M0001...)."""
    return {
        "transaction_id": _next_id("transaction_id", config.MANUAL_TXN_PREFIX, config.MANUAL_TXN_DIGITS),
        "customer_id": _next_id("customer_id", config.MANUAL_CUST_PREFIX, config.MANUAL_CUST_DIGITS),
    }


class ManualTransactionError(ValueError):
    def __init__(self, errors: list[validate.ValidationError]) -> None:
        super().__init__("; ".join(f"{e.field}: {e.message}" for e in errors))
        self.errors = errors


def save_manual_transaction(record: dict[str, Any]) -> dict[str, Any]:
    """Validate, score with predict_one, insert with source='manual', return the stored row."""
    rec = dict(record)
    rec.setdefault("timestamp", pd.Timestamp.now(tz=config.TIMEZONE))
    if rec.get("hour_of_day") is None and not isinstance(rec["timestamp"], str):
        rec["hour_of_day"] = pd.Timestamp(rec["timestamp"]).hour
    errors = validate.validate_record(rec)
    if errors:
        raise ManualTransactionError(errors)

    ids = next_manual_ids()
    rec.setdefault("transaction_id", ids["transaction_id"])
    rec.setdefault("customer_id", ids["customer_id"])
    rec["currency"] = config.CURRENCY
    rec["source"] = config.SOURCE_MANUAL
    rec["is_fraud"] = None

    scored = model_mod.predict_one(rec)
    row = {**rec, **{k: scored[k] for k in ("risk_score", "level", "decision", "reasons", "contributions", "model_version")}}
    df = pd.DataFrame([row])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    load_transactions(df)
    with get_engine().connect() as conn:
        stored = conn.execute(text("SELECT * FROM transactions WHERE transaction_id = :t"),
                              {"t": row["transaction_id"]}).mappings().one()
    return dict(stored)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    p = argparse.ArgumentParser(description="Create the PostgreSQL schema.")
    p.add_argument("--create-schema", action="store_true", default=True)
    p.parse_args()
    create_schema()


if __name__ == "__main__":
    main()
