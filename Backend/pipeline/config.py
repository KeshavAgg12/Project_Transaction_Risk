"""Single source of truth for the fraud-risk pipeline."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# --- Domain constants -------------------------------------------------------
MERCHANT_CATEGORIES = ["grocery", "restaurant", "retail", "travel", "online", "atm", "luxury"]
PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Net Banking", "Wallet"]
CURRENCY = "INR"  # country is always India; no country field anywhere
AMOUNT_MIN = 1
AMOUNT_MAX = 100_000
TIMEZONE = "Asia/Kolkata"
# --- Risk bands on risk_score (0-100): (low, high, level, decision) ----------
RISK_BANDS = [
    (0, 29, "LOW", "Approved"),
    (30, 59, "MEDIUM", "Review"),
    (60, 79, "HIGH", "Review"),
    (80, 100, "CRITICAL", "Blocked"),
]
LEVELS = [b[2] for b in RISK_BANDS]
DECISIONS = ["Approved", "Review", "Blocked"]
APPROVED_DECISION = "Approved"  # alert created for every decision != Approved
ALERT_STATUSES = ["open", "investigating", "resolved"]
DEFAULT_ALERT_STATUS = "open"

# --- Rule-based reason thresholds --------------------------------------------
HIGH_VELOCITY_THRESHOLD = 10          # transactions_last_hour > 10
DISTANCE_ANOMALY_KM = 200             # distance_from_home_km > 200
LATE_NIGHT_HOURS = {23, 0, 1, 2, 3, 4}
LARGE_AMOUNT_THRESHOLD = 20_000       # amount > 20_000
HIGH_RISK_MERCHANTS = {"online", "atm", "luxury"}

# --- Data generation ----------------------------------------------------------
N_ROWS_DEFAULT = 100_000
N_CUSTOMERS = 5_000
HISTORY_DAYS = 90
FRAUD_RATE = 0.02
FRAUD_LOOKS_NORMAL_SHARE = 0.20
NORMAL_LOOKS_SUSPICIOUS_RATE = 0.03
SOURCE_SYNTHETIC = "synthetic"
SOURCE_MANUAL = "manual"
SOURCES = [SOURCE_SYNTHETIC, SOURCE_MANUAL]

# --- Model --------------------------------------------------------------------
MODEL_TYPES = ["lightgbm", "random_forest"]
MODEL_TYPE = os.getenv("MODEL_TYPE", "lightgbm")  # "lightgbm" | "random_forest"
RANDOM_SEED = 42
FEATURES = ["amount", "hour_of_day", "merchant_encoded", "distance_from_home_km", "transactions_last_hour"]
TEST_FRACTION = 0.20
CALIBRATION_FRACTION = 0.20  # newest slice of the training window used for calibration
DECISION_THRESHOLD = 0.5     # probability threshold for precision/recall/F1
MODEL_DIR = Path(os.getenv("MODEL_DIR", BASE_DIR / "models"))
MODEL_FILENAME = "fraud_model.joblib"
MODEL_PATH = MODEL_DIR / MODEL_FILENAME
UNKNOWN_MERCHANT_CODE = -1

# --- Outputs ------------------------------------------------------------------
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", BASE_DIR / "output"))
SCORED_CSV = OUTPUT_DIR / "transactions_scored.csv"
RAW_CSV = OUTPUT_DIR / "transactions_raw.csv"
REPORT_JSON = OUTPUT_DIR / "pipeline_report.json"
DASHBOARD_PNG = OUTPUT_DIR / "dashboard.png"

# --- Manual transaction ids ---------------------------------------------------
MANUAL_TXN_PREFIX = "TXN-M"
MANUAL_TXN_DIGITS = 6
MANUAL_CUST_PREFIX = "CUST-M"
MANUAL_CUST_DIGITS = 4

# --- Database (env vars only; never hardcode credentials) ----------------------
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "fraud_risk")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
SCHEMA_SQL = BASE_DIR / "schema.sql"


def database_url() -> str:
    """Build the SQLAlchemy URL from env vars (DATABASE_URL wins if set)."""
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    from urllib.parse import quote_plus

    cred = f"{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}@" if DB_USER else ""
    return f"postgresql+psycopg2://{cred}{DB_HOST}:{DB_PORT}/{DB_NAME}"


def snapshot() -> dict:
    """Config values worth storing alongside a trained model."""
    return {
        "features": FEATURES,
        "random_seed": RANDOM_SEED,
        "test_fraction": TEST_FRACTION,
        "decision_threshold": DECISION_THRESHOLD,
        "risk_bands": RISK_BANDS,
        "merchant_categories": MERCHANT_CATEGORIES,
        "high_velocity_threshold": HIGH_VELOCITY_THRESHOLD,
        "distance_anomaly_km": DISTANCE_ANOMALY_KM,
        "late_night_hours": sorted(LATE_NIGHT_HOURS),
        "large_amount_threshold": LARGE_AMOUNT_THRESHOLD,
        "high_risk_merchants": sorted(HIGH_RISK_MERCHANTS),
    }
