"""Deterministic synthetic transaction generator (INR, India)."""
from __future__ import annotations

import argparse
import logging

import numpy as np
import pandas as pd

import config

log = logging.getLogger(__name__)

NORMAL_MERCHANT_P = [0.28, 0.20, 0.20, 0.08, 0.14, 0.07, 0.03]
FRAUD_MERCHANT_P = [0.06, 0.06, 0.08, 0.10, 0.34, 0.18, 0.18]
assert len(NORMAL_MERCHANT_P) == len(FRAUD_MERCHANT_P) == len(config.MERCHANT_CATEGORIES)

PARTIAL_OVERLAP = 0.35  # chance a single fraud signal looks normal
DAY_HOURS = np.arange(7, 22)
NIGHT_HOURS = np.array(sorted(config.LATE_NIGHT_HOURS))


def _normal_amounts(rng: np.random.Generator, n: int) -> np.ndarray:
    base = rng.lognormal(mean=np.log(1_200), sigma=0.9, size=n)
    tail = rng.random(n) < 0.04
    base[tail] = rng.uniform(8_000, 50_000, tail.sum())
    return np.clip(base, 100, 50_000)


def _fraud_amounts(rng: np.random.Generator, n: int) -> np.ndarray:
    return rng.lognormal(mean=np.log(25_000), sigma=0.7, size=n).clip(5_000, config.AMOUNT_MAX)


def _hours(rng: np.random.Generator, n: int, night_p: float) -> np.ndarray:
    night = rng.random(n) < night_p
    return np.where(night, rng.choice(NIGHT_HOURS, n), rng.choice(DAY_HOURS, n))


def _normal_block(rng: np.random.Generator, n: int) -> dict[str, np.ndarray]:
    hour = _hours(rng, n, night_p=0.04)
    distance = rng.exponential(12, n).clip(0, 150)
    velocity = rng.poisson(1.2, n)
    suspicious = rng.random(n) < config.NORMAL_LOOKS_SUSPICIOUS_RATE
    if suspicious.any():
        k = int(suspicious.sum())
        flavor = rng.random(k) < 0.5
        hour[suspicious] = np.where(flavor, rng.choice(NIGHT_HOURS, k), hour[suspicious])
        distance[suspicious] = np.where(flavor, distance[suspicious], rng.uniform(200, 800, k))
    merchant = rng.choice(config.MERCHANT_CATEGORIES, n, p=NORMAL_MERCHANT_P)
    return {"amount": _normal_amounts(rng, n), "hour": hour, "distance": distance,
            "velocity": velocity, "merchant": merchant}


def _fraud_block(rng: np.random.Generator, n: int) -> dict[str, np.ndarray]:
    hour = _hours(rng, n, night_p=0.55)
    distance = np.where(rng.random(n) < 0.6, rng.uniform(100, 1_500, n), rng.exponential(30, n))
    velocity = rng.poisson(5, n) + (rng.random(n) < 0.25) * rng.integers(5, 12, n)
    merchant = rng.choice(config.MERCHANT_CATEGORIES, n, p=FRAUD_MERCHANT_P)
    amount = _fraud_amounts(rng, n)
    # partial overlap: each signal independently reverts to "normal-looking" for some fraud rows
    weak = rng.random((n, 4)) < PARTIAL_OVERLAP
    hour = np.where(weak[:, 0], rng.choice(DAY_HOURS, n), hour)
    distance = np.where(weak[:, 1], rng.exponential(12, n).clip(0, 150), distance)
    velocity = np.where(weak[:, 2], rng.poisson(1.2, n), velocity)
    amount = np.where(weak[:, 3], rng.uniform(300, 6_000, n), amount)
    camo = rng.random(n) < config.FRAUD_LOOKS_NORMAL_SHARE
    if camo.any():
        k = int(camo.sum())
        amount[camo] = rng.uniform(100, 3_000, k)
        hour[camo] = rng.choice(DAY_HOURS, k)
        distance[camo] = rng.exponential(10, k).clip(0, 60)
        velocity[camo] = rng.poisson(1.2, k)
    return {"amount": amount, "hour": hour, "distance": distance, "velocity": velocity, "merchant": merchant}


def generate_transactions(n: int = config.N_ROWS_DEFAULT, seed: int = config.RANDOM_SEED) -> pd.DataFrame:
    """Return n synthetic transactions; identical output for identical (n, seed)."""
    rng = np.random.default_rng(seed)
    is_fraud = rng.random(n) < config.FRAUD_RATE
    n_fraud = int(is_fraud.sum())
    normal, fraud = _normal_block(rng, n - n_fraud), _fraud_block(rng, n_fraud)

    cols = {}
    for key in normal:
        dtype = object if key == "merchant" else float
        arr = np.empty(n, dtype=dtype)
        arr[~is_fraud], arr[is_fraud] = normal[key], fraud[key]
        cols[key] = arr

    end = end = pd.Timestamp.now(tz=config.TIMEZONE).normalize()
    day = rng.integers(0, config.HISTORY_DAYS, n)
    minute = rng.integers(0, 60, n)
    second = rng.integers(0, 60, n)
    ts = (end - pd.Timedelta(days=config.HISTORY_DAYS)) + pd.to_timedelta(day, unit="D") \
        + pd.to_timedelta(cols["hour"].astype(int), unit="h") \
        + pd.to_timedelta(minute, unit="m") + pd.to_timedelta(second, unit="s")
    ts = pd.Series(ts)

    df = pd.DataFrame({
        "transaction_id": [f"TXN{i:07d}" for i in range(n)],
        "timestamp": ts,
        "hour_of_day": ts.dt.hour.astype(int),
        "customer_id": [f"CUST-{c:05d}" for c in rng.integers(1, config.N_CUSTOMERS + 1, n)],
        "amount": np.round(cols["amount"], 2).clip(config.AMOUNT_MIN, config.AMOUNT_MAX),
        "merchant_category": cols["merchant"],
        "distance_from_home_km": np.round(cols["distance"], 2),
        "transactions_last_hour": cols["velocity"].astype(int),
        "payment_method": rng.choice(config.PAYMENT_METHODS, n, p=[0.45, 0.2, 0.2, 0.1, 0.05]),
        "currency": config.CURRENCY,
        "is_fraud": is_fraud.astype(int),
        "source": config.SOURCE_SYNTHETIC,
    })
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["transaction_id"] = [f"TXN{i:07d}" for i in range(n)]
    return df


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--rows", type=int, default=config.N_ROWS_DEFAULT)
    args = p.parse_args()
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = generate_transactions(args.rows)
    df.to_csv(config.RAW_CSV, index=False)
    log.info("wrote %d rows to %s (fraud rate %.2f%%)", len(df), config.RAW_CSV, df.is_fraud.mean() * 100)


if __name__ == "__main__":
    main()
