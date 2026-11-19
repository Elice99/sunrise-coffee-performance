#!/usr/bin/env python3
"""Rebuild the headline figures as assertions. Fails loudly if data changes."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = json.loads((ROOT / "outputs" / "summary.json").read_text(encoding="utf-8"))


def close(a, b, tol=0.01):
    assert abs(a - b) <= tol, f"{a} is not close to {b}"


close(S["estate"]["revenue_gbp"], 89685989.18)
close(S["estate"]["net_profit_gbp"], 16879504.07)
close(S["estate"]["net_profit_margin_pct"], 18.82, 0.01)
close(S["by_region"]["margin_pct"]["London"], 8.45, 0.01)
close(S["by_region"]["loss_month_share_pct"]["London"], 25.60, 0.01)
close(S["loyalty"]["member_share_of_revenue_pct"], 33.19, 0.01)
close(S["loyalty"]["redemption_share_of_revenue_pct"], 1.93, 0.01)
close(S["loyalty"]["corr_adoption_member_pct"], 0.998, 0.001)
assert S["loyalty"]["corr_adoption_atv"] < 0
assert S["loss_stores_latest"] == 8
assert S["formats"] == {"High-Street": 58, "Transport-Hub": 2}
assert S["quality"]["category_sum_exact_pct"] == 100.0
assert S["quality"]["net_profit_exact_pct"] == 100.0
assert S["quality"]["daily_store_days"] == 10000
assert S["quality"]["possible_store_days"] == 43800

print("QA passed: 13 checks on the Sunrise Coffee summary")
