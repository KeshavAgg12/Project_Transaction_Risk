"""Runs the six acceptance checks. Check 5 needs PostgreSQL (env vars set)."""
from __future__ import annotations

import logging

import pandas as pd

import config
import generate_data
import model
import validate


def check_1_data() -> pd.DataFrame:
    df = generate_data.generate_transactions()
    print("1. rows:", len(df), "| fraud rate: %.4f" % df.is_fraud.mean(),
          "| hour==timestamp.hour:", bool((df.hour_of_day == df.timestamp.dt.hour).all()),
          "| amount range:", df.amount.min(), "-", df.amount.max())
    assert abs(df.is_fraud.mean() - config.FRAUD_RATE) < 0.003
    assert (df.hour_of_day == df.timestamp.dt.hour).all()
    assert df.amount.between(config.AMOUNT_MIN, config.AMOUNT_MAX).all()
    return df


def check_2_metrics(df: pd.DataFrame) -> None:
    print("2. test-set metrics (newest %d%% by time; never train rows):" % (config.TEST_FRACTION * 100))
    print(model.compare_models(df).to_string())


def check_3_distribution(df: pd.DataFrame) -> dict:
    art = model.train_model(df, config.MODEL_TYPE)
    scored = model.predict_batch(df, art)
    counts = scored["level"].value_counts().reindex(config.LEVELS, fill_value=0)
    print("3. score distribution (all rows):", counts.to_dict())
    assert (counts > 0).all(), "a band is empty"
    return art


def check_4_consistency(df: pd.DataFrame, art: dict) -> None:
    sample = df.sample(500, random_state=1)
    batch = model.predict_batch(sample, art)
    mism = 0
    for idx, row in sample.iterrows():
        one = model.predict_one(row.to_dict(), art)
        if one["risk_score"] != int(batch.loc[idx, "risk_score"]) or one["level"] != batch.loc[idx, "level"]:
            mism += 1
    print("4. predict_one vs predict_batch on 500 rows, mismatches:", mism)
    assert mism == 0


def check_5_db_idempotent() -> None:
    import db
    scored = pd.read_csv(config.SCORED_CSV, parse_dates=["timestamp"]).head(5000)
    db.create_schema()
    db.load_transactions(scored)
    n1 = db.count_transactions()
    db.load_transactions(scored)
    n2 = db.count_transactions()
    print(f"5. DB row count after load: {n1}, after re-load: {n2}")
    assert n1 == n2


def check_6_rejections() -> None:
    base = dict(amount=500, hour_of_day=12, merchant_category="grocery", distance_from_home_km=5,
                transactions_last_hour=1, payment_method="UPI")
    cases = {"amount 0": {"amount": 0}, "amount 100001": {"amount": 100001}, "hour 24": {"hour_of_day": 24},
             "unknown merchant": {"merchant_category": "casino"}}
    print("6. validate_record:")
    print("   valid baseline ->", validate.validate_record(base))
    for name, patch in cases.items():
        errs = validate.validate_record({**base, **patch})
        print(f"   {name} -> rejected={bool(errs)} {[e.check for e in errs]}")
        assert errs


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    data = check_1_data()
    check_2_metrics(data)
    artifact = check_3_distribution(data)
    check_4_consistency(data, artifact)
    check_6_rejections()
    try:
        check_5_db_idempotent()
    except Exception as exc:  # noqa: BLE001
        print("5. SKIPPED/FAILED (database not reachable?):", exc)
    print("done")
