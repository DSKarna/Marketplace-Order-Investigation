#!/usr/bin/env python3
"""Render a compact static overview from the reproducible CSV exports.

Optional dependency: matplotlib. The core SQL analysis uses only Python's
standard library.
"""
import csv
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed"
OUT = ROOT / "assets/analysis_overview.png"


def read(name):
    with (DATA / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


months, states, categories = read("monthly_orders.csv"), read("state_comparison.csv"), read("category_comparison.csv")
labels = [r["month"] for r in months]
values = [int(r["delivered_orders"]) for r in months]
top_states = states[:5]
top_categories = categories[:5]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titleweight": "bold", "axes.titlelocation": "left"})
fig = plt.figure(figsize=(13.2, 8.4), facecolor="#ffffff", layout="constrained")
grid = fig.add_gridspec(2, 2, height_ratios=[1.12, 1])
trend = fig.add_subplot(grid[0, :])
state_ax = fig.add_subplot(grid[1, 0])
category_ax = fig.add_subplot(grid[1, 1])

trend.plot(range(len(values)), values, color="#164c74", linewidth=2.6, marker="o", markersize=3.5)
nov_i, dec_i = labels.index("2017-11"), labels.index("2017-12")
trend.scatter([nov_i, dec_i], [values[nov_i], values[dec_i]], color=["#dd7c35", "#b34040"], zorder=3, s=55)
trend.annotate("Nov 2017\n7,289", (nov_i, values[nov_i]), xytext=(-5, 19), textcoords="offset points", ha="center", fontsize=9, color="#394652")
trend.annotate("Dec 2017\n5,513", (dec_i, values[dec_i]), xytext=(30, -29), textcoords="offset points", ha="center", fontsize=9, color="#394652")
trend.set_title("Delivered orders by purchase month", pad=12)
trend.set_ylim(bottom=0)
trend.set_ylabel("Orders")
trend.set_xticks(range(0, len(labels), 2), [labels[i] for i in range(0, len(labels), 2)], rotation=35, ha="right")
trend.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
trend.grid(axis="y", color="#e7ebef", linewidth=.8)
trend.set_axisbelow(True)

state_names = [r["state"] for r in top_states][::-1]
state_values = [-int(r["order_change"]) for r in top_states][::-1]
bars = state_ax.barh(state_names, state_values, color="#407da3", height=.62)
state_ax.set_title("Largest state declines", pad=10)
state_ax.set_xlabel("Fewer delivered orders, Dec vs Nov 2017")
state_ax.bar_label(bars, fmt="%d", padding=4, fontsize=9)
state_ax.set_xlim(0, max(state_values) * 1.22)
state_ax.grid(axis="x", color="#e7ebef", linewidth=.8)
state_ax.set_axisbelow(True)

cat_names = [r["category"].replace("_", " ") for r in top_categories][::-1]
cat_values = [-float(r["merchandise_change_brl"]) for r in top_categories][::-1]
bars = category_ax.barh(cat_names, cat_values, color="#dd935e", height=.62)
category_ax.set_title("Largest category declines", pad=10)
category_ax.set_xlabel("Decrease in product value (BRL), Dec vs Nov 2017")
category_ax.bar_label(bars, labels=[f"{v:,.0f}" for v in cat_values], padding=4, fontsize=9)
category_ax.set_xlim(0, max(cat_values) * 1.30)
category_ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
category_ax.grid(axis="x", color="#e7ebef", linewidth=.8)
category_ax.set_axisbelow(True)

fig.suptitle("Marketplace order investigation", x=.01, ha="left", fontsize=18, weight="bold", color="#18232d")
fig.text(.01, -.035, "Source: Olist public Brazilian e-commerce data. Product value excludes freight; analysis is descriptive.",
         fontsize=9, color="#647481")
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=170, bbox_inches="tight", facecolor="white")
print(f"Wrote {OUT}")
