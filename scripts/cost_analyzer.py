from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd


# ---------------------------
# Config (MVP thresholds)
# ---------------------------
NAT_DAILY_THRESHOLD = 140.0          # flag if NAT Gateway daily cost >= this
EC2_SHARE_THRESHOLD = 0.45           # flag if EC2 >= 45% of total spend
DEV_TO_PROD_RATIO_THRESHOLD = 0.60   # flag if dev spend is >= 60% of prod spend


def load_costs(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)

    required_cols = {"date", "service", "region", "environment", "cost"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in CSV: {sorted(missing)}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if df["date"].isna().any():
        bad_rows = df[df["date"].isna()]
        raise ValueError(f"Invalid date rows found:\n{bad_rows}")

    df["cost"] = pd.to_numeric(df["cost"], errors="coerce")
    if df["cost"].isna().any():
        bad_rows = df[df["cost"].isna()]
        raise ValueError(f"Invalid cost rows found:\n{bad_rows}")

    df["service"] = df["service"].astype(str).str.strip()
    df["region"] = df["region"].astype(str).str.strip()
    df["environment"] = df["environment"].astype(str).str.strip().str.lower()

    return df


def kpis(df: pd.DataFrame) -> dict:
    total = float(df["cost"].sum())

    by_service = (
        df.groupby("service", as_index=False)["cost"]
        .sum()
        .sort_values("cost", ascending=False)
    )

    by_env = (
        df.groupby("environment", as_index=False)["cost"]
        .sum()
        .sort_values("cost", ascending=False)
    )

    by_region = (
        df.groupby("region", as_index=False)["cost"]
        .sum()
        .sort_values("cost", ascending=False)
    )

    return {
        "total_cost": total,
        "by_service": by_service,
        "by_env": by_env,
        "by_region": by_region,
    }


def generate_insights(df: pd.DataFrame, kpi: dict) -> list[str]:
    insights: list[str] = []

    total = kpi["total_cost"]
    by_service = kpi["by_service"]
    by_env = kpi["by_env"]

    # Top driver
    if len(by_service) > 0 and total > 0:
        top = by_service.iloc[0]
        share = float(top["cost"]) / total
        insights.append(
            f"Top cost driver: {top['service']} = ${top['cost']:.2f} ({share:.0%} of total)."
        )

    # EC2 share alert
    if total > 0:
        ec2_cost = float(by_service[by_service["service"].str.upper() == "EC2"]["cost"].sum())
        ec2_share = ec2_cost / total if total else 0.0
        if ec2_share >= EC2_SHARE_THRESHOLD and ec2_cost > 0:
            insights.append(
                f"EC2 dominates spend: ${ec2_cost:.2f} ({ec2_share:.0%}). Consider rightsizing / scheduling / savings plans."
            )

    # NAT daily spikes
    nat = df[df["service"].str.lower() == "nat gateway"].copy()
    if not nat.empty:
        nat_daily = nat.groupby("date", as_index=False)["cost"].sum()
        spikes = nat_daily[nat_daily["cost"] >= NAT_DAILY_THRESHOLD]
        for _, row in spikes.iterrows():
            d = row["date"].date().isoformat()
            insights.append(
                f"NAT Gateway spike detected on {d}: ${row['cost']:.2f}. Review egress patterns, NAT usage, and private subnet routing."
            )

    # Dev vs prod anomaly
    env_map = {str(r["environment"]): float(r["cost"]) for _, r in by_env.iterrows()}
    dev = env_map.get("dev", 0.0)
    prod = env_map.get("prod", 0.0)
    if prod > 0 and dev / prod >= DEV_TO_PROD_RATIO_THRESHOLD:
        insights.append(
            f"Dev spend is high vs prod: dev=${dev:.2f} vs prod=${prod:.2f} ({dev/prod:.0%}). Check non-prod scheduling and idle resources."
        )

    if not insights:
        insights.append("No major waste signals detected with current thresholds (MVP).")

    return insights


def main() -> int:
    # Default path assumes project structure: scripts/ -> ../data/cloud_costs.csv
    default_csv = Path(__file__).resolve().parents[1] / "data" / "cloud_costs.csv"
    csv_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else default_csv

    df = load_costs(csv_path)
    kpi = kpis(df)
    insights = generate_insights(df, kpi)

    print("\n=== FinOps KPIs (MVP) ===")
    print(f"Total spend: ${kpi['total_cost']:.2f}\n")

    print("Spend by service:")
    print(kpi["by_service"].to_string(index=False))
    print("\nSpend by environment:")
    print(kpi["by_env"].to_string(index=False))
    print("\nSpend by region:")
    print(kpi["by_region"].to_string(index=False))

    print("\n=== Insights / Waste Signals ===")
    for i, msg in enumerate(insights, start=1):
        print(f"{i}. {msg}")

    # Optional: export a simple report for the dashboard to consume later
    out_dir = Path(__file__).resolve().parents[1] / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    kpi["by_service"].to_csv(out_dir / "kpi_by_service.csv", index=False)
    kpi["by_env"].to_csv(out_dir / "kpi_by_env.csv", index=False)
    kpi["by_region"].to_csv(out_dir / "kpi_by_region.csv", index=False)

    pd.DataFrame({"insight": insights}).to_csv(out_dir / "insights.csv", index=False)

    print("\nExported:")
    print(f"- {out_dir / 'kpi_by_service.csv'}")
    print(f"- {out_dir / 'kpi_by_env.csv'}")
    print(f"- {out_dir / 'kpi_by_region.csv'}")
    print(f"- {out_dir / 'insights.csv'}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
