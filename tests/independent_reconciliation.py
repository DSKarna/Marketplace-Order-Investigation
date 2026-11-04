"""Optional independent reconciliation using pandas (not required to reproduce)."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
orders = pd.read_csv(RAW / "olist_orders_dataset.csv")
customers = pd.read_csv(RAW / "olist_customers_dataset.csv")
items = pd.read_csv(RAW / "olist_order_items_dataset.csv")
products = pd.read_csv(RAW / "olist_products_dataset.csv")
translation = pd.read_csv(RAW / "product_category_name_translation.csv", encoding="utf-8-sig")

period = orders.loc[(orders.order_status == "delivered") &
                    (orders.order_purchase_timestamp >= "2017-11-01") &
                    (orders.order_purchase_timestamp < "2018-01-01")].copy()
period["month"] = period.order_purchase_timestamp.str.slice(0, 7)
assert period.groupby("month").order_id.nunique().to_dict() == {"2017-11": 7289, "2017-12": 5513}

by_state = (period.merge(customers, on="customer_id", how="left", validate="one_to_one")
            .groupby(["customer_state", "month"]).order_id.nunique().unstack(fill_value=0))
sql_states = pd.read_csv(ROOT / "data/processed/state_comparison.csv").set_index("state")
for state, row in by_state.iterrows():
    assert int(row.get("2017-11", 0)) == int(sql_states.loc[state, "nov_orders"])
    assert int(row.get("2017-12", 0)) == int(sql_states.loc[state, "dec_orders"])

lines = (period[["order_id", "month"]].merge(items, on="order_id", validate="one_to_many")
         .merge(products[["product_id", "product_category_name"]], on="product_id", how="left", validate="many_to_one")
         .merge(translation, on="product_category_name", how="left", validate="many_to_one"))
lines["category"] = lines.product_category_name_english.fillna(lines.product_category_name).fillna("Unclassified")
lines["price_cents"] = (lines.price * 100).round().astype(int)
by_category = lines.groupby(["category", "month"]).price_cents.sum().unstack(fill_value=0)
sql_categories = pd.read_csv(ROOT / "data/processed/category_comparison.csv").set_index("category")
for category, row in by_category.iterrows():
    assert int(row.get("2017-11", 0)) == round(float(sql_categories.loc[category, "nov_merchandise_brl"]) * 100)
    assert int(row.get("2017-12", 0)) == round(float(sql_categories.loc[category, "dec_merchandise_brl"]) * 100)
print("Independent pandas reconciliation passed: monthly order counts, every state, and every category.")
