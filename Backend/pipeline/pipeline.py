"""Orchestration: Ingest -> Validate -> Model (train or load) -> Score & Report."""
from __future__ import annotations

import argparse
import json
import logging
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd

import config
import generate_data
import model as model_mod
import validate

log = logging.getLogger("pipeline")

STATUS_SUCCESS, STATUS_WARNING, STATUS_FAILED = "success", "warning", "failed"


@dataclass
class StageResult:
    name: str
    started_at: str
    finished_at: str
    duration_ms: int
    rows_in: int
    rows_out: int
    error_count: int
    status: str
    message: str


@dataclass
class StageOutcome:
    """What a stage function returns; the runner adds timing."""
    rows_in: int
    rows_out: int
    error_count: int = 0
    status: str = STATUS_SUCCESS
    message: str = ""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def run_stage(name: str, fn: Callable[[], StageOutcome], rows_in_fallback: int = 0) -> StageResult:
    """Run one stage, always returning a recorded result (exceptions become status=failed)."""
    start, t0 = _now(), time.perf_counter()
    try:
        out = fn()
    except Exception as exc:  # noqa: BLE001 - a failed stage must be recorded, not lost
        log.exception("stage %s failed", name)
        out = StageOutcome(rows_in_fallback, 0, 1, STATUS_FAILED, f"{type(exc).__name__}: {exc}")
    end = _now()
    res = StageResult(name, start.isoformat(), end.isoformat(), int((time.perf_counter() - t0) * 1000),
                      out.rows_in, out.rows_out, out.error_count, out.status, out.message)
    log.info("[%s] %s in %d ms (rows %d -> %d) %s", name, res.status, res.duration_ms,
             res.rows_in, res.rows_out, res.message)
    return res


# --- Ingest -------------------------------------------------------------------
def ingest(source: str, rows: int, csv_path: Path | None) -> pd.DataFrame:
    if source == "synthetic":
        return generate_data.generate_transactions(rows)
    if source == "csv":
        df = pd.read_csv(csv_path or config.RAW_CSV)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        if "source" not in df:
            df["source"] = config.SOURCE_SYNTHETIC
        if "currency" not in df:
            df["currency"] = config.CURRENCY
        return df
    if source == "db":
        import db
        return db.read_transactions()
    raise ValueError(f"unknown source {source!r}")


# --- Model ----------------------------------------------------------------------
def train_or_load(df: pd.DataFrame, train: bool, model_type: str) -> tuple[dict[str, Any], str]:
    """Return (artifact, message). Trains when requested or when no saved model exists."""
    if not train and config.MODEL_PATH.exists():
        art = model_mod.load_model()
        return art, f"loaded {art['version']}"
    if "is_fraud" not in df or df["is_fraud"].isna().all():
        raise ValueError("cannot train: no is_fraud labels in the ingested data")
    labelled = df[df["is_fraud"].notna()]
    art = model_mod.train_model(labelled, model_type)
    model_mod.save_model(art)
    model_mod.load_model()  # warm the cache with the saved artifact
    why = "trained (requested)" if train else "trained (no saved model found)"
    return art, f"{why} {art['version']}; test F1={art['metrics']['f1']:.3f}"


# --- Score & report ------------------------------------------------------------
def score_all(df: pd.DataFrame, artifact: dict[str, Any]) -> pd.DataFrame:
    scored = model_mod.predict_batch(df, artifact)
    out = pd.concat([df, scored], axis=1)
    out["alert_status"] = out["decision"].map(
        lambda d: config.DEFAULT_ALERT_STATUS if d != config.APPROVED_DECISION else None)
    return out


def write_csv(scored: pd.DataFrame, path: Path = config.SCORED_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = scored.copy()
    for col in ("reasons", "contributions"):
        out[col] = out[col].map(lambda v: None if v is None else json.dumps(v))
    out.to_csv(path, index=False)


def build_summary(run_id: str, started: datetime, scored: pd.DataFrame | None, artifact: dict[str, Any] | None,
                  stages: list[StageResult], status: str, source: str) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "run_id": run_id, "started_at": started.isoformat(), "finished_at": _now().isoformat(),
        "status": status, "source": source, "total_rows": 0 if scored is None else len(scored),
        "model_version": artifact["version"] if artifact else None,
        "per_level": {lv: 0 for lv in config.LEVELS},
        "per_decision": {d: 0 for d in config.DECISIONS},
        "alerts_created": 0,
    }
    if scored is not None:
        summary["per_level"].update({k: int(v) for k, v in scored["level"].value_counts().items()})
        summary["per_decision"].update({k: int(v) for k, v in scored["decision"].value_counts().items()})
        summary["alerts_created"] = int((scored["decision"] != config.APPROVED_DECISION).sum())
    if artifact:
        summary["test_metrics"] = artifact["metrics"]
    summary["stages"] = [asdict(s) for s in stages]
    return summary


def overall_status(stages: list[StageResult]) -> str:
    if any(s.status == STATUS_FAILED for s in stages):
        return STATUS_FAILED
    return STATUS_WARNING if any(s.status == STATUS_WARNING for s in stages) else STATUS_SUCCESS


# --- Orchestration ---------------------------------------------------------------
def run_pipeline(source: str = "synthetic", rows: int = config.N_ROWS_DEFAULT, train: bool = False,
                 model_type: str = config.MODEL_TYPE, csv_path: Path | None = None,
                 load_db: bool = False) -> dict[str, Any]:
    run_id, started = uuid.uuid4().hex[:12], _now()
    state: dict[str, Any] = {"df": None, "artifact": None, "scored": None, "report": None}
    stages: list[StageResult] = []

    def s_ingest() -> StageOutcome:
        state["df"] = ingest(source, rows, csv_path)
        return StageOutcome(0, len(state["df"]), message=f"source={source}")

    def s_validate() -> StageOutcome:
        df = state["df"]
        report = validate.validate_dataframe(df)
        state["report"] = report
        if report.has_structural_errors:
            return StageOutcome(len(df), 0, len(report.structural_errors), STATUS_FAILED,
                                "; ".join(report.structural_errors))
        bad = report.total_rows - report.valid_rows
        state["df"] = df[validate.valid_rows_mask(df)].reset_index(drop=True)
        status = STATUS_WARNING if bad else STATUS_SUCCESS
        return StageOutcome(len(df), len(state["df"]), bad, status,
                            f"{bad} invalid rows dropped; high-velocity rows={report.high_velocity_count}")

    def s_model() -> StageOutcome:
        df = state["df"]
        state["artifact"], msg = train_or_load(df, train, model_type)
        status = STATUS_WARNING if "no saved model" in msg else STATUS_SUCCESS
        return StageOutcome(len(df), len(df), 0, status, msg)

    def s_report() -> StageOutcome:
        df = state["df"]
        scored = score_all(df, state["artifact"])
        state["scored"] = scored
        write_csv(scored)
        msg = f"wrote {config.SCORED_CSV.name}"
        if load_db:
            import db
            db.create_schema()
            db.save_model_version(state["artifact"])
            n = db.load_transactions(scored)
            msg += f"; upserted {n} rows to PostgreSQL"
        return StageOutcome(len(df), len(scored), 0, STATUS_SUCCESS, msg)

    plan = [("Ingest", s_ingest), ("Validate", s_validate), ("Model", s_model), ("Score & Report", s_report)]
    for name, fn in plan:
        res = run_stage(name, fn, rows_in_fallback=0 if state["df"] is None else len(state["df"]))
        stages.append(res)
        if res.status == STATUS_FAILED:
            log.error("halting after failed stage %s", name)
            break

    status = overall_status(stages)
    summary = build_summary(run_id, started, state["scored"], state["artifact"], stages, status, source)
    summary["validation"] = state["report"].to_dict() if state["report"] else None

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.REPORT_JSON.write_text(json.dumps(summary, indent=2, default=str))
    if load_db:
        try:
            import db
            db.save_run(summary, summary["stages"])
        except Exception:  # noqa: BLE001
            log.exception("could not persist run metadata")
    log.info("run %s finished: %s (%d rows) levels=%s", run_id, status, summary["total_rows"], summary["per_level"])
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fraud-risk pipeline")
    p.add_argument("--train", action="store_true", help="retrain instead of loading the saved model")
    p.add_argument("--rows", type=int, default=config.N_ROWS_DEFAULT)
    p.add_argument("--model", choices=config.MODEL_TYPES, default=config.MODEL_TYPE)
    p.add_argument("--source", choices=["synthetic", "csv", "db"], default="synthetic")
    p.add_argument("--csv", type=Path, default=None, help="CSV path when --source csv")
    p.add_argument("--load-db", action="store_true", help="also upsert results into PostgreSQL")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    a = parse_args(argv)
    summary = run_pipeline(a.source, a.rows, a.train, a.model, a.csv, a.load_db)
    return 0 if summary["status"] != STATUS_FAILED else 1


if __name__ == "__main__":
    raise SystemExit(main())
