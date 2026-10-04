# Fraud-risk pipeline

A modular batch pipeline that generates (or ingests) card transactions, validates them, trains or loads a
calibrated fraud model, scores **every** row, and loads results into PostgreSQL. No API or frontend code is included.

> **Honest note:** the model is trained on **synthetic data**. Scores demonstrate that the pipeline works end to end
> and are **not real-world fraud probabilities**. Do not use them to make real decisions.

## Layout

| File | Purpose |
|---|---|
| `config.py` | Single source of truth: categories, bands, thresholds, model type, paths, DB env vars |
| `generate_data.py` | Deterministic synthetic data (seeded), with realistic feature overlap |
| `validate.py` | `validate_record()` (single record, API-reusable) and `validate_dataframe()` (batch report) |
| `model.py` | `train_model`, `compare_models`, `load_model`, `predict_batch`, `predict_one` |
| `pipeline.py` | Orchestration: Ingest -> Validate -> Model (train/load) -> Score & Report |
| `db.py`, `schema.sql`, `create_schema.py` | PostgreSQL schema, idempotent bulk load, run logging, manual-transaction helpers |
| `dashboard.py` | Local matplotlib report from the scored CSV (INR, score-band chart) |
| `acceptance_checks.py` | Runs the six acceptance checks |

## Stages

1. **Ingest** - source is `synthetic`, `csv` or `db`.
2. **Validate** - nulls, amount range, hour, merchant, distance, velocity, payment method, duplicate IDs. Invalid rows are dropped and counted; the run halts only on structural errors (missing columns, no rows).
3. **Model** - loads the saved artifact by default; `--train` retrains (also trains automatically, with a warning, if none exists).
4. **Score & Report** - scores all rows, assigns level / decision / reasons / contributions, writes `output/transactions_scored.csv` and `output/pipeline_report.json`, optionally upserts to PostgreSQL.

Every stage records name, started_at, finished_at, duration_ms, rows_in, rows_out, error_count, status and message, even when it fails.

## Model

- Features: `amount, hour_of_day, merchant_encoded, distance_from_home_km, transactions_last_hour`.
- **Time-based split**: oldest 64% train, next 16% calibration, newest 20% test. Metrics are computed only on the test slice.
- Imbalance is handled with class weighting, then probabilities are recalibrated (Platt scaling on the calibration slice), so `risk_score = round(probability * 100)`. The F1 threshold is chosen on the calibration slice, never on test.
- Switch with `MODEL_TYPE` in `config.py` / `.env` or `--model lightgbm|random_forest`.
- LightGBM also returns per-transaction contributions (`pred_contrib`, log-odds space of the uncalibrated booster; for relative ranking only). Random forest returns `null`.
- The saved artifact (`models/fraud_model.joblib`) holds model, encoder, features, model_type, version (`lgbm-YYYYMMDD-HHMM`), trained_at, metrics, feature importances and a config snapshot.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env        # fill in DB_* values (never commit .env)
```

## Running

```bash
python pipeline.py --train --rows 100000 --model lightgbm   # train + score
python pipeline.py                                          # score with the saved model
python pipeline.py --source csv --csv output/transactions_raw.csv
python generate_data.py --rows 100000                       # write raw CSV only
python dashboard.py                                         # build output/dashboard.png
python acceptance_checks.py                                 # acceptance checks
```

### Loading to PostgreSQL

```bash
python create_schema.py                  # creates tables and indexes (safe to re-run)
python pipeline.py --load-db             # scores and upserts transactions, run, stages, model version
```

Loads use chunked `execute_values` with `ON CONFLICT (transaction_id) DO UPDATE`, so re-running never duplicates rows
and existing `alert_status` values (e.g. `investigating`) are preserved. An alert (`alert_status='open'`) is created
for every decision other than `Approved`. The CSV is always written, so you can inspect results before trusting the DB.

## Helpers for a future API (importable, no API built)

```python
import db
db.next_manual_ids()                 # {'transaction_id': 'TXN-M000001', 'customer_id': 'CUST-M0001'}
db.save_manual_transaction(record)   # validates, scores with predict_one, inserts source='manual', returns stored row
```

## Risk bands

| Score | Level | Decision |
|---|---|---|
| 0-29 | LOW | Approved |
| 30-59 | MEDIUM | Review |
| 60-79 | HIGH | Review |
| 80-100 | CRITICAL | Blocked |
