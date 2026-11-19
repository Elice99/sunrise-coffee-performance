#!/usr/bin/env python3
"""Reproduce the Sunrise Coffee performance review from the supplied CSVs.

Reads the five source tables in data/ and writes outputs/summary.json.
Every figure used in the portfolio case study comes from this script.
No random steps, no network calls, no manual workbook edits.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs" / "summary.json"


def load():
    return (
        pd.read_csv(DATA / "dim_store.csv"),
        pd.read_csv(DATA / "dim_product.csv"),
        pd.read_csv(DATA / "dim_date.csv", parse_dates=["full_date"]),
        pd.read_csv(DATA / "fact_daily_sales.csv"),
        pd.read_csv(DATA / "fact_store_monthly_profitability.csv"),
    )


def build() -> dict:
    store, prod, date, daily, monthly = load()
    m = monthly.merge(
        store[["store_id", "store_format", "region", "loyalty_adoption_rate", "store_name"]],
        on="store_id", how="left",
    )
    d = daily.merge(store[["store_id", "store_format", "region"]], on="store_id", how="left")
    d = d.merge(
        date[["date_id", "year", "month_number", "quarter", "day_of_week", "is_weekend",
              "is_uk_bank_holiday", "uk_trading_calendar"]],
        on="date_id", how="left",
    )

    r: dict = {}
    r["rows"] = {"store": len(store), "product": len(prod), "date": len(date),
                 "daily": len(daily), "monthly": len(monthly)}
    r["date_range"] = [str(date.full_date.min().date()), str(date.full_date.max().date())]
    r["formats"] = store.store_format.value_counts().to_dict()
    r["regions"] = int(store.region.nunique())
    r["stores_by_region"] = store.region.value_counts().to_dict()

    rev = float(m.total_monthly_revenue_gbp.sum())
    profit = float(m.net_profit_gbp.sum())
    r["estate"] = {
        "revenue_gbp": rev,
        "net_profit_gbp": profit,
        "net_profit_margin_pct": profit / rev * 100,
        "cogs_gbp": float(m.total_monthly_cogs_gbp.sum()),
        "rent_gbp": float(m.monthly_rent_gbp.sum()),
        "staffing_gbp": float(m.monthly_staffing_cost_gbp.sum()),
        "loyalty_redemption_gbp": float(m.loyalty_redemption_cost_gbp.sum()),
    }

    yr = m.groupby(m.month_id.str[:4]).agg(
        revenue=("total_monthly_revenue_gbp", "sum"), profit=("net_profit_gbp", "sum"))
    yr["margin_pct"] = yr.profit / yr.revenue * 100
    r["yearly"] = json.loads(yr.round(4).to_json())

    def cut(key):
        g = m.groupby(key).agg(
            revenue=("total_monthly_revenue_gbp", "sum"),
            profit=("net_profit_gbp", "sum"),
            rev_per_sqft=("revenue_per_sqft_gbp", "mean"),
            footfall=("avg_daily_footfall", "mean"),
        )
        g["margin_pct"] = g.profit / g.revenue * 100
        loss = m.profitability_status.isin(["Loss-Making", "Structural-Loss"])
        g["loss_month_share_pct"] = loss.groupby(m[key]).mean() * 100
        return g.sort_values("margin_pct", ascending=False)

    r["by_format"] = json.loads(cut("store_format").round(4).to_json())
    r["by_region"] = json.loads(cut("region").round(4).to_json())

    # Loyalty. Store-level correlations use recomputed ATV because the supplied
    # avg_transaction_value_gbp column is rounded to two decimals.
    sad = m.groupby("store_id").agg(
        adoption=("loyalty_adoption_rate", "mean"),
        member_pct=("loyalty_member_revenue_pct", "mean"),
        member_spend=("loyalty_member_spend_gbp", "sum"),
        redemption=("loyalty_redemption_cost_gbp", "sum"),
        fmt=("store_format", "first"),
    )
    sad["atv"] = d.groupby("store_id").apply(
        lambda x: x.total_revenue_gbp.sum() / x.total_transactions.sum(),
        include_groups=False,
    )
    member_spend = float(m.loyalty_member_spend_gbp.sum())
    redemption = float(m.loyalty_redemption_cost_gbp.sum())
    r["loyalty"] = {
        "corr_adoption_member_pct": float(sad.adoption.corr(sad.member_pct)),
        "corr_adoption_atv": float(sad.adoption.corr(sad.atv)),
        "member_spend_gbp": member_spend,
        "redemption_gbp": redemption,
        "net_contribution_gbp": member_spend - redemption,
        "member_share_of_revenue_pct": member_spend / rev * 100,
        "redemption_share_of_revenue_pct": redemption / rev * 100,
    }
    r["loyalty_by_format"] = json.loads(sad.groupby("fmt").agg(
        adoption=("adoption", "mean"), member_pct=("member_pct", "mean")
    ).round(4).to_json())

    # Revenue mix from the daily fact.
    cats = ["espresso_revenue_gbp", "filter_revenue_gbp", "food_revenue_gbp", "retail_beans_revenue_gbp"]
    mix = d[cats].sum()
    r["mix"] = {c: {"gbp": float(v), "pct": float(v / mix.sum() * 100)} for c, v in mix.items()}
    mixyr = d.groupby("year")[cats].sum()
    r["mix_by_year_pct"] = json.loads((mixyr.div(mixyr.sum(axis=1), axis=0) * 100).round(3).to_json())

    prod["margin_pct"] = (prod.unit_price_gbp - prod.unit_cost_gbp) / prod.unit_price_gbp * 100
    r["product_margin_by_category"] = json.loads(
        prod.groupby("product_category").margin_pct.agg(["mean", "min", "max", "count"]).round(3).to_json())

    # Temporal cuts are per recorded store-day, not a full estate daily census.
    r["bank_holiday"] = json.loads(d.groupby("is_uk_bank_holiday").agg(
        rows=("daily_sale_id", "count"), avg_revenue=("total_revenue_gbp", "mean")).round(3).to_json())
    r["bank_holiday_by_format"] = json.loads(d.groupby(["store_format", "is_uk_bank_holiday"]).agg(
        rows=("daily_sale_id", "count"), avg_revenue=("total_revenue_gbp", "mean")).round(3).to_json())
    r["weekend"] = json.loads(d.groupby("is_weekend").agg(
        rows=("daily_sale_id", "count"), avg_revenue=("total_revenue_gbp", "mean")).round(3).to_json())
    q = m.assign(year=m.month_id.str[:4],
                 quarter=m.month_id.str[-2:].astype(int).map(lambda x: (x - 1) // 3 + 1))
    r["quarterly"] = json.loads(q.groupby(["year", "quarter"]).agg(
        revenue=("total_monthly_revenue_gbp", "sum"),
        profit=("net_profit_gbp", "sum")).round(2).to_json())
    mo = m.assign(year=m.month_id.str[:4], month=m.month_id.str[-2:]).groupby(["year", "month"]).net_profit_gbp.sum()
    r["best_months"] = json.loads(mo.nlargest(5).round(2).to_json())
    r["worst_months"] = json.loads(mo.nsmallest(5).round(2).to_json())

    # Store movement and current risk list.
    piv = m.assign(year=m.month_id.str[:4]).pivot_table(
        index=["store_id", "store_name", "store_format", "region"],
        columns="year", values="net_profit_gbp", aggfunc="sum").reset_index()
    piv["change"] = piv["2024"] - piv["2023"]
    cols = ["store_name", "store_format", "region", "2023", "2024", "change"]
    r["top_improvers"] = json.loads(piv.nlargest(5, "change")[cols].round(2).to_json(orient="records"))
    r["top_deteriorators"] = json.loads(piv.nsmallest(5, "change")[cols].round(2).to_json(orient="records"))
    latest = m[m.month_id == "2024-12"]
    r["status_latest"] = latest.profitability_status.value_counts().to_dict()
    r["loss_stores_latest"] = int(latest.profitability_status.isin(["Loss-Making", "Structural-Loss"]).sum())
    r["loss_by_region_latest"] = json.loads(
        latest.assign(loss=latest.profitability_status.isin(["Loss-Making", "Structural-Loss"]))
        .groupby("region").loss.sum().to_json())
    r["structural_store_latest"] = json.loads(
        latest[latest.profitability_status == "Structural-Loss"][["store_name", "region", "net_profit_gbp"]]
        .round(2).to_json(orient="records"))

    # Data quality checks.
    derived_atv = daily.total_revenue_gbp / daily.total_transactions
    ratio = daily.avg_transaction_value_gbp / derived_atv
    r["quality"] = {
        "category_sum_exact_pct": float(np.isclose(d[ cats ].sum(axis=1), d.total_revenue_gbp).mean() * 100),
        "net_profit_exact_pct": float(np.isclose(
            m.net_profit_gbp,
            m.total_monthly_revenue_gbp - m.total_monthly_cogs_gbp - m.monthly_rent_gbp
            - m.monthly_staffing_cost_gbp - m.loyalty_redemption_cost_gbp).mean() * 100),
        "atv_within_rounding_pct": float(((ratio >= 0.998) & (ratio <= 1.002)).mean() * 100),
        "atv_max_abs_pct_gap": float((ratio - 1).abs().max() * 100),
        "nulls": {
            "loyalty_member_revenue_pct": int(m.loyalty_member_revenue_pct.isna().sum()),
            "avg_daily_footfall": int(m.avg_daily_footfall.isna().sum()),
            "seating_capacity": int(store.seating_capacity.isna().sum()),
        },
        "dim_date_columns": list(date.columns),
        "daily_extra_vs_dictionary": sorted(set(daily.columns) - {
            "daily_sale_id", "store_id", "date_id", "product_id", "total_revenue_gbp",
            "total_transactions", "avg_transaction_value_gbp", "loyalty_transactions",
            "loyalty_redemption_cost_gbp", "footfall", "espresso_revenue_gbp",
            "filter_revenue_gbp", "food_revenue_gbp", "retail_beans_revenue_gbp",
            "daily_gross_profit_gbp", "shift_pattern", "staff_count", "total_staff_hours"}),
        "daily_store_days": len(daily),
        "possible_store_days": int(len(store) * len(date)),
    }
    return r


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result = build()
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes)")
