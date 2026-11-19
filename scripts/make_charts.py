#!/usr/bin/env python3
"""Generate the six report charts from data/ (no manual edits)."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = json.loads((ROOT / "outputs" / "summary.json").read_text(encoding="utf-8"))
CHARTS = ROOT / "outputs" / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

TEAL = "#0f766e"
RED = "#b91c1c"
GREY = "#94a3b8"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})


def save(fig, name):
    path = CHARTS / name
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", path.relative_to(ROOT))


# 1. Regional margin
reg = SUMMARY["by_region"]["margin_pct"]
reg = dict(sorted(reg.items(), key=lambda kv: kv[1]))
fig, ax = plt.subplots(figsize=(9, 6))
colors = [RED if k == "London" else TEAL for k in reg]
ax.barh(list(reg), list(reg.values()), color=colors)
for i, v in enumerate(reg.values()):
    ax.text(v + 0.3, i, f"{v:.1f}%", va="center", fontsize=10)
ax.set_xlabel("Net profit margin (%)")
ax.set_title("Net profit margin by region, 2023-2024")
ax.set_xlim(0, max(reg.values()) * 1.15)
save(fig, "01_region_margin.png")

# 2. Loss store-month share
loss = SUMMARY["by_region"]["loss_month_share_pct"]
loss = dict(sorted(loss.items(), key=lambda kv: kv[1]))
fig, ax = plt.subplots(figsize=(9, 6))
colors = [RED if k == "London" else TEAL for k in loss]
ax.barh(list(loss), list(loss.values()), color=colors)
for i, v in enumerate(loss.values()):
    ax.text(v + 0.3, i, f"{v:.1f}%", va="center", fontsize=10)
ax.set_xlabel("Store-months classed Loss-Making or Structural-Loss (%)")
ax.set_title("Loss-making store-months by region")
ax.set_xlim(0, max(loss.values()) * 1.2)
save(fig, "02_region_loss.png")

# 3. Loyalty scatter
import pandas as pd
s = pd.read_csv(ROOT / "data" / "dim_store.csv")
m = pd.read_csv(ROOT / "data" / "fact_store_monthly_profitability.csv")
adopt = s.groupby("store_id").loyalty_adoption_rate.mean()
member = m.groupby("store_id").loyalty_member_revenue_pct.mean()
fig, ax = plt.subplots(figsize=(7, 6))
ax.scatter(adopt * 100, member * 100, s=28, color=TEAL, alpha=0.75)
lims = [0, max(adopt.max(), member.max()) * 100 + 3]
ax.plot(lims, lims, ls="--", color=GREY, lw=1, label="equal share")
ax.set_xlim(lims); ax.set_ylim(lims)
ax.set_xlabel("Loyalty adoption rate (%)")
ax.set_ylabel("Revenue from loyalty members (%)")
ax.set_title(f"Adoption and member revenue move together (r = {SUMMARY['loyalty']['corr_adoption_member_pct']:.3f})")
ax.legend(frameon=False, loc="upper left")
save(fig, "03_loyalty_scatter.png")

# 4. Mix by year
mix = SUMMARY["mix_by_year_pct"]
labels = ["Espresso", "Filter", "Food", "Retail beans"]
keys = ["espresso_revenue_gbp", "filter_revenue_gbp", "food_revenue_gbp", "retail_beans_revenue_gbp"]
x = np.arange(len(labels)); w = 0.36
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(x - w/2, [mix[k]["2023"] for k in keys], w, label="2023", color=GREY)
ax.bar(x + w/2, [mix[k]["2024"] for k in keys], w, label="2024", color=TEAL)
ax.set_xticks(x); ax.set_xticklabels(labels)
ax.set_ylabel("Share of recorded daily revenue (%)")
ax.set_title("Revenue mix barely moved, 2023 to 2024")
ax.legend(frameon=False)
save(fig, "04_mix_by_year.png")

# 5. Bank holiday revenue by format
import ast
bh = SUMMARY["bank_holiday_by_format"]["avg_revenue"]
parsed = {ast.literal_eval(k): v for k, v in bh.items()}
formats = sorted({k[0] for k in parsed})
x = np.arange(len(formats)); w = 0.36
normal = [parsed.get((f, False), 0) for f in formats]
holiday = [parsed.get((f, True), 0) for f in formats]
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(x - w/2, normal, w, label="Normal trading day", color=TEAL)
ax.bar(x + w/2, holiday, w, label="Bank holiday", color=RED)
ax.set_xticks(x); ax.set_xticklabels(formats)
ax.set_ylabel("Average revenue per recorded store-day (GBP)")
ax.set_title("Bank holidays are quieter, not busier")
ax.legend(frameon=False)
save(fig, "05_bank_holiday.png")

# 6. Store movements
imp = SUMMARY["top_improvers"][:4]
det = SUMMARY["top_deteriorators"][:4]
rows = [(r["store_name"].replace("Sunrise Coffee ", ""), r["change"]) for r in det + imp]
rows.sort(key=lambda kv: kv[1])
fig, ax = plt.subplots(figsize=(9, 6))
colors = [RED if v < 0 else TEAL for _, v in rows]
ax.barh([k for k, _ in rows], [v for _, v in rows], color=colors)
ax.axvline(0, color="black", lw=0.8)
ax.set_xlabel("Change in annual net profit, 2023 to 2024 (GBP)")
ax.set_title("Biggest store profit movements")
save(fig, "06_store_moves.png")
