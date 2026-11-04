#!/usr/bin/env python3
"""Build the one-page case-study PDF (requires reportlab)."""
import csv
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/Marketplace_Case_Study.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)
data = ROOT / "data/processed"
metrics = json.loads((data / "key_metrics.json").read_text(encoding="utf-8"))
nov = metrics["focus"]["november"]["delivered_orders"]
dec = metrics["focus"]["december"]["delivered_orders"]
change_rate = (dec / nov - 1) if nov else 0
with (data / "daily_orders_nov_dec.csv").open(encoding="utf-8", newline="") as f:
    nov24 = next(int(row["delivered_orders"]) for row in csv.DictReader(f) if row["day"] == "2017-11-24")
with (data / "monthly_orders.csv").open(encoding="utf-8", newline="") as f:
    monthly = list(csv.DictReader(f))

W, H = A4
left, right = 42, W - 42
navy = colors.HexColor("#153F60")
ink = colors.HexColor("#172C3B")
muted = colors.HexColor("#5D7180")
grid = colors.HexColor("#DEE6EC")
orange = colors.HexColor("#DB7D37")
red = colors.HexColor("#AE4342")
c = canvas.Canvas(str(OUT), pagesize=A4)
c.setTitle("Marketplace Order Investigation")
c.setAuthor("Independent marketplace analysis")


def text(x, y, string, size=9, color=ink, bold=False):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawString(x, y, string)


def right_text(x, y, string, size=9, color=ink, bold=False):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawRightString(x, y, string)


def section(y, title):
    text(left, y, title, 10, navy, True)


text(left, H-49, "Marketplace Order Investigation", 20, ink, True)
text(left, H-67, "Brazil | Delivered purchase cohorts | Jan 2017 - Jul 2018", 9, muted)
c.setStrokeColor(grid)
c.line(left, H-78, right, H-78)

kpi_y = H - 101
for x, label, value, color in [
    (left, "NOV 2017 ORDERS", f"{nov:,}", navy),
    (left+171, "DEC 2017 ORDERS", f"{dec:,}", navy),
    (left+342, "MONTHLY CHANGE", f"{change_rate:.1%}", red),
]:
    text(x, kpi_y, label, 8, muted, True)
    text(x, kpi_y-24, value, 19, color, True)

section(H-157, "Delivered orders by purchase month")
chart_left, chart_right = left+36, right-8
chart_bottom, chart_top = H-307, H-177
for tick in (0, 2000, 4000, 6000, 8000):
    y = chart_bottom + tick / 8000 * (chart_top-chart_bottom)
    c.setStrokeColor(grid)
    c.line(chart_left, y, chart_right, y)
    right_text(chart_left-7, y-3, f"{tick/1000:.0f}k", 7, muted)

points = []
for i, row in enumerate(monthly):
    x = chart_left + i*(chart_right-chart_left)/(len(monthly)-1)
    y = chart_bottom + int(row["delivered_orders"])/8000*(chart_top-chart_bottom)
    points.append((x, y))
c.setStrokeColor(navy)
c.setLineWidth(1.8)
for a, b in zip(points, points[1:]):
    c.line(a[0], a[1], b[0], b[1])
for index, color, label, offset in [(10, orange, f"Nov: {nov:,}", 10), (11, red, f"Dec: {dec:,}", -15)]:
    x, y = points[index]
    c.setFillColor(color)
    c.circle(x, y, 3.5, fill=1, stroke=0)
    text(x+6, y+offset, label, 8, color, True)
for i in (0, 4, 8, 12, 16, 18):
    x, _ = points[i]
    text(x-15, chart_bottom-14, monthly[i]["month"], 7, muted)

section(H-348, "Where the change was concentrated")
left_table_x, right_table_x = left, left+255
text(left_table_x, H-368, "CUSTOMER STATE", 8, muted, True)
right_text(left_table_x+215, H-368, "ORDER CHANGE", 8, muted, True)
text(right_table_x, H-368, "PRODUCT CATEGORY", 8, muted, True)
right_text(right, H-368, "VALUE CHANGE", 8, muted, True)
for i, (state, category) in enumerate(zip(metrics["largest_state_decreases"][:3], metrics["largest_category_decreases"][:3])):
    y = H-388-i*20
    text(left_table_x, y, state["state"], 9)
    right_text(left_table_x+215, y, f"{state['order_change']:,}", 9, red)
    label = category["category"].replace("_", " ")
    text(right_table_x, y, label, 8.8)
    right_text(right, y, f"{category['merchandise_change_brl']:,.0f} BRL", 8.8, red)

box_y, box_h = H-492, 49
c.setFillColor(colors.HexColor("#EDF3F6"))
c.roundRect(left, box_y, right-left, box_h, 4, fill=1, stroke=0)
text(left+12, box_y+31, "One unusually large day", 9, navy, True)
text(left+12, box_y+16, f"November 24 accounted for {nov24:,} orders ({nov24/nov:.1%} of November).", 9, ink)

section(H-522, "Method and interpretation")
text(left, H-540, "Orders are grouped by purchase date and counted once; only delivered orders are included.", 8.7)
text(left, H-554, "Product value sums item prices in BRL and excludes freight. It is not platform revenue.", 8.7)
text(left, H-568, "The results identify patterns to investigate; the data does not establish their causes.", 8.7)

section(H-602, "Next investigation")
text(left, H-620, "Check promotion timing and traffic around November 24 against comparable periods.", 8.7)
text(left, H-634, "Review availability and seller activity in the states and categories with the largest declines.", 8.7)

c.setStrokeColor(grid)
c.line(left, 71, right, 71)
text(left, 55, "Source: Olist Brazilian E-Commerce Public Dataset | CC BY-NC-SA 4.0", 7.8, muted)
text(left, 43, "kaggle.com/datasets/olistbr/brazilian-ecommerce", 7.8, navy)
c.linkURL("https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce", (left, 40, left+280, 53), relative=0)
c.showPage()
c.save()
print(f"Wrote {OUT}")
