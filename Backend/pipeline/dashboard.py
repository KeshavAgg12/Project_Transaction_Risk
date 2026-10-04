"""Local matplotlib report built from the scored CSV (amounts in INR)."""
from __future__ import annotations

import logging

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import config

log = logging.getLogger(__name__)
RUPEE = "₹"
LEVEL_COLORS = {"LOW": "#2a9d8f", "MEDIUM": "#e9c46a", "HIGH": "#f4a261", "CRITICAL": "#d62828"}


def _rupees(x: float, _pos=None) -> str:
    return f"{RUPEE}{x:,.0f}"


def build_dashboard(csv_path=config.SCORED_CSV, out_path=config.DASHBOARD_PNG) -> None:
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    fig, ax = plt.subplots(2, 2, figsize=(14, 9))

    counts = df["level"].value_counts().reindex(config.LEVELS, fill_value=0)
    bars = ax[0, 0].bar(counts.index, counts.values, color=[LEVEL_COLORS[l] for l in counts.index])
    ax[0, 0].bar_label(bars, fmt="{:,.0f}")
    ax[0, 0].set(title="Score-band distribution", ylabel="Transactions")

    ax[0, 1].hist(df["risk_score"], bins=50, color="#264653")
    for _, high, _, _ in config.RISK_BANDS[:-1]:
        ax[0, 1].axvline(high + 0.5, color="grey", ls="--", lw=0.8)
    ax[0, 1].set(title="Risk score histogram", xlabel="risk_score", ylabel="Transactions")
    ax[0, 1].set_yscale("log")

    alerts = df[df["decision"] != config.APPROVED_DECISION]
    by_merchant = alerts.groupby("merchant_category")["amount"].sum().reindex(config.MERCHANT_CATEGORIES, fill_value=0)
    ax[1, 0].bar(by_merchant.index, by_merchant.values, color="#e76f51")
    ax[1, 0].yaxis.set_major_formatter(_rupees)
    ax[1, 0].set(title=f"Flagged amount by merchant ({RUPEE})")
    ax[1, 0].tick_params(axis="x", rotation=30)

    daily = df.set_index("timestamp").resample("D")["decision"].apply(lambda s: (s != config.APPROVED_DECISION).sum())
    ax[1, 1].plot(daily.index, daily.values, color="#6a4c93")
    ax[1, 1].set(title="Alerts per day", ylabel="Alerts")

    total_amt = df["amount"].sum()
    fig.suptitle(f"Fraud-risk report - {len(df):,} transactions, {_rupees(total_amt)} volume, "
                 f"{len(alerts):,} alerts", fontsize=13)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    log.info("saved %s", out_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    build_dashboard()
