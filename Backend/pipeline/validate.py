"""Validation: single-record (API-reusable) and batch."""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field, asdict
from typing import Any

import pandas as pd

import config

log = logging.getLogger(__name__)

REQUIRED_FIELDS = ["amount", "hour_of_day", "merchant_category", "distance_from_home_km",
                   "transactions_last_hour", "payment_method"]
BATCH_REQUIRED = ["transaction_id"] + REQUIRED_FIELDS


@dataclass(frozen=True)
class ValidationError:
    field: str
    check: str
    message: str


@dataclass
class CheckResult:
    name: str
    passed: bool
    failed_count: int
    detail: str = ""


@dataclass
class ValidationReport:
    total_rows: int
    valid_rows: int
    checks: list[CheckResult] = field(default_factory=list)
    high_velocity_count: int = 0
    structural_errors: list[str] = field(default_factory=list)

    @property
    def has_structural_errors(self) -> bool:
        return bool(self.structural_errors)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _is_null(v: Any) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and not _is_null(v)


def validate_record(record: dict) -> list[ValidationError]:
    """Validate one transaction. Pure; returns [] when valid."""
    errs: list[ValidationError] = []
    for f in REQUIRED_FIELDS:
        if _is_null(record.get(f)):
            errs.append(ValidationError(f, "nulls", f"{f} is required"))
    if errs:
        return errs

    amount = record["amount"]
    if not _is_number(amount) or not config.AMOUNT_MIN <= amount <= config.AMOUNT_MAX:
        errs.append(ValidationError("amount", "amount_range",
                                    f"amount must be in {config.AMOUNT_MIN}..{config.AMOUNT_MAX}"))
    hour = record["hour_of_day"]
    if not _is_number(hour) or int(hour) != hour or not 0 <= hour <= 23:
        errs.append(ValidationError("hour_of_day", "hour_range", "hour_of_day must be an integer 0-23"))
    if record["merchant_category"] not in config.MERCHANT_CATEGORIES:
        errs.append(ValidationError("merchant_category", "merchant_category", "unknown merchant_category"))
    dist = record["distance_from_home_km"]
    if not _is_number(dist) or dist < 0:
        errs.append(ValidationError("distance_from_home_km", "distance_non_negative", "distance must be >= 0"))
    vel = record["transactions_last_hour"]
    if not _is_number(vel) or vel < 0 or int(vel) != vel:
        errs.append(ValidationError("transactions_last_hour", "velocity_valid",
                                    "transactions_last_hour must be a non-negative integer"))
    if record["payment_method"] not in config.PAYMENT_METHODS:
        errs.append(ValidationError("payment_method", "payment_method", "unknown payment_method"))
    return errs


def _check(name: str, bad: pd.Series, detail: str) -> CheckResult:
    n = int(bad.sum())
    return CheckResult(name, n == 0, n, detail if n else "")


def validate_dataframe(df: pd.DataFrame) -> ValidationReport:
    """Vectorised batch validation. Missing required columns are structural errors."""
    report = ValidationReport(total_rows=len(df), valid_rows=0)
    missing = [c for c in BATCH_REQUIRED if c not in df.columns]
    if missing:
        report.structural_errors.append(f"missing columns: {missing}")
        return report
    if df.empty:
        report.structural_errors.append("no rows to process")
        return report

    nulls = df[BATCH_REQUIRED].isna().any(axis=1)
    num = lambda c: pd.to_numeric(df[c], errors="coerce")  # noqa: E731
    amount, hour, dist, vel = num("amount"), num("hour_of_day"), num("distance_from_home_km"), num("transactions_last_hour")
    bad_masks = {
        "nulls": nulls,
        "amount_range": ~amount.between(config.AMOUNT_MIN, config.AMOUNT_MAX) & ~nulls,
        "hour_range": (~hour.between(0, 23) | (hour % 1 != 0)) & ~nulls,
        "merchant_category": ~df["merchant_category"].isin(config.MERCHANT_CATEGORIES) & ~nulls,
        "distance_non_negative": ~(dist >= 0) & ~nulls,
        "velocity_valid": (~(vel >= 0) | (vel % 1 != 0)) & ~nulls,
        "payment_method": ~df["payment_method"].isin(config.PAYMENT_METHODS) & ~nulls,
        "duplicate_transaction_id": df["transaction_id"].duplicated(keep="first"),
    }
    details = {
        "nulls": "null in a required column",
        "amount_range": f"outside {config.AMOUNT_MIN}..{config.AMOUNT_MAX}",
        "hour_range": "hour not an integer in 0-23",
        "merchant_category": f"not in {config.MERCHANT_CATEGORIES}",
        "distance_non_negative": "negative or non-numeric distance",
        "velocity_valid": "negative or non-integer velocity",
        "payment_method": f"not in {config.PAYMENT_METHODS}",
        "duplicate_transaction_id": "repeated transaction_id",
    }
    any_bad = pd.Series(False, index=df.index)
    for name, mask in bad_masks.items():
        report.checks.append(_check(name, mask, details[name]))
        any_bad |= mask
    report.valid_rows = int((~any_bad).sum())
    report.high_velocity_count = int((vel > config.HIGH_VELOCITY_THRESHOLD).sum())
    for c in report.checks:
        if not c.passed:
            log.warning("validation: %s failed on %d rows (%s)", c.name, c.failed_count, c.detail)
    log.info("validation: %d/%d rows valid; high-velocity rows: %d",
             report.valid_rows, report.total_rows, report.high_velocity_count)
    return report


def valid_rows_mask(df: pd.DataFrame) -> pd.Series:
    """Boolean mask of rows passing every row-level check (used to drop bad rows)."""
    mask = pd.Series(True, index=df.index)
    num = lambda c: pd.to_numeric(df[c], errors="coerce")  # noqa: E731
    mask &= df[BATCH_REQUIRED].notna().all(axis=1)
    mask &= num("amount").between(config.AMOUNT_MIN, config.AMOUNT_MAX)
    h = num("hour_of_day")
    mask &= h.between(0, 23) & (h % 1 == 0)
    mask &= df["merchant_category"].isin(config.MERCHANT_CATEGORIES)
    mask &= num("distance_from_home_km") >= 0
    v = num("transactions_last_hour")
    mask &= (v >= 0) & (v % 1 == 0)
    mask &= df["payment_method"].isin(config.PAYMENT_METHODS)
    mask &= ~df["transaction_id"].duplicated(keep="first")
    return mask
