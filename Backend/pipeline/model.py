"""Training, evaluation and prediction. Train and predict are fully separate."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)

import config

log = logging.getLogger(__name__)

VERSION_PREFIX = {"lightgbm": "lgbm", "random_forest": "rf"}
CALIBRATION_METHOD = "sigmoid"  # "sigmoid" (Platt) or "isotonic"


# --- Encoder -------------------------------------------------------------------
class MerchantEncoder:
    """Fixed category->int mapping from config; unknown categories map to -1."""

    def __init__(self, categories: list[str] | None = None) -> None:
        self.categories = list(categories or config.MERCHANT_CATEGORIES)
        self.mapping = {c: i for i, c in enumerate(self.categories)}

    def transform(self, values: pd.Series) -> np.ndarray:
        return values.map(self.mapping).fillna(config.UNKNOWN_MERCHANT_CODE).astype(int).to_numpy()


# --- Calibrated model wrapper ---------------------------------------------------
class CalibratedModel:
    """A fitted base classifier plus a probability calibrator fitted on held-out data."""

    def __init__(self, base: Any, calibrator: Any, method: str) -> None:
        self.base, self.calibrator, self.method = base, calibrator, method

    def raw_proba(self, X: pd.DataFrame) -> np.ndarray:
        return self.base.predict_proba(X)[:, 1]

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        raw = self.raw_proba(X)
        if self.method == "isotonic":
            return self.calibrator.predict(raw)
        logit = np.log(np.clip(raw, 1e-6, 1 - 1e-6) / (1 - np.clip(raw, 1e-6, 1 - 1e-6)))
        return self.calibrator.predict_proba(logit.reshape(-1, 1))[:, 1]


def _fit_calibrator(raw: np.ndarray, y: np.ndarray, method: str) -> Any:
    if method == "isotonic":
        return IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(raw, y)
    logit = np.log(np.clip(raw, 1e-6, 1 - 1e-6) / (1 - np.clip(raw, 1e-6, 1 - 1e-6)))
    return LogisticRegression(C=1e6).fit(logit.reshape(-1, 1), y)


# --- Features -------------------------------------------------------------------
def build_features(df: pd.DataFrame, encoder: MerchantEncoder) -> pd.DataFrame:
    X = pd.DataFrame(index=df.index)
    X["amount"] = pd.to_numeric(df["amount"]).astype(float)
    X["hour_of_day"] = pd.to_numeric(df["hour_of_day"]).astype(int)
    X["merchant_encoded"] = encoder.transform(df["merchant_category"])
    X["distance_from_home_km"] = pd.to_numeric(df["distance_from_home_km"]).astype(float)
    X["transactions_last_hour"] = pd.to_numeric(df["transactions_last_hour"]).astype(int)
    return X[config.FEATURES]


# --- Training ---------------------------------------------------------------------
def time_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Oldest -> train, next -> calibration, newest TEST_FRACTION -> test (all by timestamp)."""
    d = df.sort_values("timestamp").reset_index(drop=True)
    n_test = int(len(d) * config.TEST_FRACTION)
    train_all, test = d.iloc[: len(d) - n_test], d.iloc[len(d) - n_test:]
    n_cal = int(len(train_all) * config.CALIBRATION_FRACTION)
    return train_all.iloc[: len(train_all) - n_cal], train_all.iloc[len(train_all) - n_cal:], test


def _make_base(model_type: str, y_train: np.ndarray) -> Any:
    if model_type == "lightgbm":
        pos_weight = float((y_train == 0).sum() / max((y_train == 1).sum(), 1))
        return LGBMClassifier(n_estimators=150, learning_rate=0.08, num_leaves=15, min_child_samples=40,
                              subsample=0.8, subsample_freq=1, colsample_bytree=0.9,
                              scale_pos_weight=min(pos_weight, 10.0), importance_type="gain",
                              random_state=config.RANDOM_SEED, n_jobs=-1, verbose=-1)
    if model_type == "random_forest":
        return RandomForestClassifier(n_estimators=300, min_samples_leaf=20, class_weight="balanced_subsample",
                                      random_state=config.RANDOM_SEED, n_jobs=-1)
    raise ValueError(f"unknown model_type {model_type!r}; expected one of {config.MODEL_TYPES}")


def _best_f1_threshold(y: np.ndarray, proba: np.ndarray) -> float:
    """Pick the F1-maximising threshold on the calibration slice (never on test)."""
    grid = np.linspace(0.05, 0.95, 91)
    scores = [f1_score(y, proba >= t, zero_division=0) for t in grid]
    return float(grid[int(np.argmax(scores))])


def evaluate(y_true: np.ndarray, proba: np.ndarray, threshold: float) -> dict[str, Any]:
    pred = proba >= threshold
    cm = confusion_matrix(y_true, pred, labels=[0, 1])
    return {
        "precision": float(precision_score(y_true, pred, zero_division=0)),
        "recall": float(recall_score(y_true, pred, zero_division=0)),
        "f1": float(f1_score(y_true, pred, zero_division=0)),
        "pr_auc": float(average_precision_score(y_true, proba)),
        "roc_auc": float(roc_auc_score(y_true, proba)),
        "confusion_matrix": cm.tolist(),  # [[TN, FP], [FN, TP]]
        "threshold": float(threshold),
        "n_test": int(len(y_true)),
        "n_test_fraud": int(y_true.sum()),
    }


def make_version(model_type: str, now: datetime | None = None) -> str:
    return f"{VERSION_PREFIX[model_type]}-{(now or datetime.now()):%Y%m%d-%H%M}"


def train_model(df: pd.DataFrame, model_type: str = config.MODEL_TYPE) -> dict[str, Any]:
    """Train + calibrate + evaluate on the newest slice. Returns the artifact dict (not saved)."""
    train, cal, test = time_split(df)
    encoder = MerchantEncoder()
    X_tr, X_cal, X_te = (build_features(p, encoder) for p in (train, cal, test))
    y_tr, y_cal, y_te = (p["is_fraud"].astype(int).to_numpy() for p in (train, cal, test))
    log.info("split: train=%d calibration=%d test=%d (time-based)", len(train), len(cal), len(test))

    base = _make_base(model_type, y_tr).fit(X_tr, y_tr)
    raw_cal = base.predict_proba(X_cal)[:, 1]
    model = CalibratedModel(base, _fit_calibrator(raw_cal, y_cal, CALIBRATION_METHOD), CALIBRATION_METHOD)
    threshold = _best_f1_threshold(y_cal, model.predict_proba(X_cal))
    metrics = evaluate(y_te, model.predict_proba(X_te), threshold)  # held-out test ONLY
    metrics["train_window_end"] = str(train["timestamp"].max())
    metrics["test_window_start"] = str(test["timestamp"].min())

    importances = dict(zip(config.FEATURES, (float(v) for v in base.feature_importances_)))
    total = sum(importances.values()) or 1.0
    importances = {k: v / total for k, v in importances.items()}
    now = datetime.now()
    return {
        "model": model, "encoder": encoder, "features": config.FEATURES, "model_type": model_type,
        "version": make_version(model_type, now), "trained_at": now.isoformat(timespec="seconds"),
        "metrics": metrics, "feature_importances": importances, "config": config.snapshot(),
    }


def save_model(artifact: dict[str, Any], path=config.MODEL_PATH) -> None:
    path = config.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, path)
    _CACHE.pop(str(path), None)
    log.info("saved model %s -> %s", artifact["version"], path)


def compare_models(df: pd.DataFrame) -> pd.DataFrame:
    """Train both model types on the same time split; return a test-set metrics table."""
    rows = {}
    for mt in config.MODEL_TYPES:
        m = train_model(df, mt)["metrics"]
        rows[mt] = {k: m[k] for k in ("precision", "recall", "f1", "pr_auc", "roc_auc", "threshold")}
        rows[mt]["confusion_matrix"] = m["confusion_matrix"]
    table = pd.DataFrame(rows).T
    log.info("model comparison (test set only):\n%s", table.to_string())
    return table


# --- Loading / prediction -----------------------------------------------------------
_CACHE: dict[str, dict[str, Any]] = {}


def load_model(path=config.MODEL_PATH) -> dict[str, Any]:
    """Load the artifact once per path and cache it."""
    key = str(path)
    if key not in _CACHE:
        _CACHE[key] = joblib.load(path)
        log.info("loaded model %s", _CACHE[key]["version"])
    return _CACHE[key]


def risk_level(score: int) -> tuple[str, str]:
    for low, high, level, decision in config.RISK_BANDS:
        if low <= score <= high:
            return level, decision
    raise ValueError(f"score {score} outside 0-100")


def triggered_reasons(df: pd.DataFrame) -> list[list[str]]:
    """Rule-based reason codes per row, using thresholds from config."""
    rules = {
        "HIGH_VELOCITY": df["transactions_last_hour"] > config.HIGH_VELOCITY_THRESHOLD,
        "DISTANCE_ANOMALY": df["distance_from_home_km"] > config.DISTANCE_ANOMALY_KM,
        "LATE_NIGHT": df["hour_of_day"].isin(config.LATE_NIGHT_HOURS),
        "LARGE_AMOUNT": df["amount"] > config.LARGE_AMOUNT_THRESHOLD,
        "HIGH_RISK_MERCHANT": df["merchant_category"].isin(config.HIGH_RISK_MERCHANTS),
    }
    flags = pd.DataFrame(rules)
    return [[code for code in flags.columns if row[code]] for row in flags.to_dict("records")]


def _contributions(artifact: dict[str, Any], X: pd.DataFrame) -> list[dict[str, float] | None]:
    if artifact["model_type"] != "lightgbm":
        return [None] * len(X)
    # LightGBM pred_contrib values live in log-odds space of the *uncalibrated* booster and
    # are for relative ranking of features only; they do not sum to risk_score.
    booster = artifact["model"].base.booster_
    contrib = booster.predict(X, pred_contrib=True)[:, :-1]  # drop the bias column
    return [dict(zip(artifact["features"], map(float, row))) for row in contrib]


def predict_batch(df: pd.DataFrame, artifact: dict[str, Any] | None = None) -> pd.DataFrame:
    """Score rows. The single code path used by predict_one as well."""
    artifact = artifact or load_model()
    X = build_features(df, artifact["encoder"])
    proba = artifact["model"].predict_proba(X)
    score = np.clip(np.rint(proba * 100), 0, 100).astype(int)
    levels = [risk_level(int(s)) for s in score]
    out = pd.DataFrame(index=df.index)
    out["risk_score"] = score
    out["level"] = [l for l, _ in levels]
    out["decision"] = [d for _, d in levels]
    out["reasons"] = triggered_reasons(df)
    out["contributions"] = _contributions(artifact, X)
    out["model_version"] = artifact["version"]
    return out


def predict_one(record: dict, artifact: dict[str, Any] | None = None) -> dict[str, Any]:
    """Score a single transaction dict via predict_batch."""
    res = predict_batch(pd.DataFrame([record]), artifact).iloc[0]
    return {
        "risk_score": int(res["risk_score"]), "level": res["level"], "decision": res["decision"],
        "reasons": list(res["reasons"]), "contributions": res["contributions"],
        "model_version": res["model_version"],
    }
