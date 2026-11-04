#!/usr/bin/env python3
"""Rebuild a portable SQLite database and reproduce the published CSVs.

Requires Python 3.9+ and the five Olist CSVs in data/raw. No pip installs.
Run from any directory: python scripts/run_analysis.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sqlite3
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
SQL = ROOT / "sql"
DATABASE = ROOT / "data" / "olist.sqlite"

SOURCES = {
    "orders": "olist_orders_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "products": "olist_products_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}


def number_cents(value: str) -> int:
    try:
        n = Decimal(value)
        if not n.is_finite() or n * 100 != (n * 100).to_integral_value():
            raise ValueError(f"Value is not a finite amount with cent precision: {value!r}")
        return int(n * 100)
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"Invalid monetary amount: {value!r}") from exc


def rows(path: Path):
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        yield from csv.DictReader(handle)


def load_tables(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "INSERT INTO orders VALUES (?,?,?,?,?,?,?,?)",
        ((r["order_id"], r["customer_id"], r["order_status"], r["order_purchase_timestamp"],
          r["order_approved_at"] or None, r["order_delivered_carrier_date"] or None,
          r["order_delivered_customer_date"] or None, r["order_estimated_delivery_date"] or None)
         for r in rows(RAW / SOURCES["orders"])),
    )
    conn.executemany(
        "INSERT INTO customers VALUES (?,?,?,?,?)",
        ((r["customer_id"], r["customer_unique_id"], r["customer_zip_code_prefix"],
          r["customer_city"], r["customer_state"]) for r in rows(RAW / SOURCES["customers"])),
    )
    conn.executemany(
        "INSERT INTO order_items VALUES (?,?,?,?,?,?,?)",
        ((r["order_id"], int(r["order_item_id"]), r["product_id"], r["seller_id"],
          r["shipping_limit_date"], number_cents(r["price"]), number_cents(r["freight_value"]))
         for r in rows(RAW / SOURCES["order_items"])),
    )
    conn.executemany(
        "INSERT INTO products VALUES (?,?)",
        ((r["product_id"], r["product_category_name"] or None) for r in rows(RAW / SOURCES["products"])),
    )
    conn.executemany(
        "INSERT INTO category_translation VALUES (?,?)",
        ((r["product_category_name"], r["product_category_name_english"] or None)
         for r in rows(RAW / SOURCES["category_translation"])),
    )


def execute_export(conn: sqlite3.Connection, query_file: str, target: str):
    cursor = conn.execute((SQL / query_file).read_text(encoding="utf-8"))
    headers = [d[0] for d in cursor.description]
    records = [dict(zip(headers, row)) for row in cursor.fetchall()]
    with (OUT / target).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    return records


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    missing = [str(RAW / name) for name in SOURCES.values() if not (RAW / name).is_file()]
    if missing:
        raise FileNotFoundError("Missing input CSVs: " + ", ".join(missing))
    OUT.mkdir(parents=True, exist_ok=True)
    if DATABASE.exists():
        DATABASE.unlink()
    conn = sqlite3.connect(DATABASE)
    try:
        conn.executescript((SQL / "01_schema.sql").read_text(encoding="utf-8"))
        with conn:
            load_tables(conn)
        monthly = execute_export(conn, "02_monthly_orders.sql", "monthly_orders.csv")
        states = execute_export(conn, "03_state_comparison.sql", "state_comparison.csv")
        cities = execute_export(conn, "04_city_comparison.sql", "city_comparison.csv")
        categories = execute_export(conn, "05_category_comparison.sql", "category_comparison.csv")
        checks = execute_export(conn, "06_quality_checks.sql", "quality_checks.csv")
        daily = execute_export(conn, "07_daily_orders.sql", "daily_orders_nov_dec.csv")

        lookup = {row["month"]: row for row in monthly}
        nov, dec = lookup["2017-11"], lookup["2017-12"]
        assert sum(x["nov_orders"] for x in states) == nov["delivered_orders"]
        assert sum(x["dec_orders"] for x in states) == dec["delivered_orders"]
        assert sum(x["nov_orders"] for x in cities) == nov["delivered_orders"]
        assert sum(x["dec_orders"] for x in cities) == dec["delivered_orders"]
        assert sum(x["delivered_orders"] for x in daily if x["day"].startswith("2017-11")) == nov["delivered_orders"]
        assert sum(x["delivered_orders"] for x in daily if x["day"].startswith("2017-12")) == dec["delivered_orders"]
        for month, field in [(nov, "nov_merchandise_brl"), (dec, "dec_merchandise_brl")]:
            total_cents = sum(round(row[field] * 100) for row in categories)
            assert total_cents == round(month["merchandise_brl"] * 100)

        metrics = {
            "scope": "Delivered orders purchased Jan 2017 through Jul 2018; focus Nov vs Dec 2017",
            "focus": {"november": nov, "december": dec},
            "daily_orders": {"november": nov["delivered_orders"] / 30, "december": dec["delivered_orders"] / 31},
            "top_purchase_days": sorted(daily, key=lambda x: x["delivered_orders"], reverse=True)[:5],
            "largest_state_decreases": [x for x in states if x["order_change"] < 0][:5],
            "largest_city_decreases": [x for x in cities if x["order_change"] < 0][:5],
            "largest_category_decreases": [x for x in categories if x["merchandise_change_brl"] < 0][:5],
            "quality": {x["check_name"]: x["result"] for x in checks},
            "source_sha256": {filename: sha256(RAW / filename) for filename in SOURCES.values()},
        }
        (OUT / "key_metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"nov_orders": nov["delivered_orders"], "dec_orders": dec["delivered_orders"],
                          "order_change": dec["order_change"], "order_change_rate": dec["order_change_rate"],
                          "quality": metrics["quality"]}, indent=2))
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, sqlite3.Error, AssertionError, FileNotFoundError) as error:
        print(f"Analysis failed: {error}", file=sys.stderr)
        raise
