"""Small behavior tests for order grain and category reconciliation."""
import sqlite3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AnalysisGrainTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.executescript((ROOT / "sql/01_schema.sql").read_text(encoding="utf-8"))
        self.conn.executemany("INSERT INTO customers VALUES (?,?,?,?,?)", [
            ("c1", "u1", "01000", "alpha", "SP"), ("c2", "u2", "02000", "beta", "RJ"),
            ("c3", "u3", "01000", "alpha", "SP"),
        ])
        self.conn.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?)", [
            ("n1", "c1", "delivered", "2017-11-02 10:00:00", None, None, None, None),
            ("n2", "c2", "delivered", "2017-11-03 10:00:00", None, None, None, None),
            ("d1", "c3", "delivered", "2017-12-03 10:00:00", None, None, None, None),
            ("x1", "c1", "canceled", "2017-12-04 10:00:00", None, None, None, None),
        ])
        self.conn.executemany("INSERT INTO products VALUES (?,?)", [("p1", "alimentos"), ("p2", None)])
        self.conn.execute("INSERT INTO category_translation VALUES (?,?)", ("alimentos", "food"))
        self.conn.executemany("INSERT INTO order_items VALUES (?,?,?,?,?,?,?)", [
            ("n1", 1, "p1", "s", "", 1000, 0),
            ("n1", 2, "p1", "s", "", 2000, 0),
            ("n2", 1, "p2", "s", "", 500, 0),
            ("d1", 1, "p1", "s", "", 4000, 0),
            ("x1", 1, "p1", "s", "", 999900, 0),
        ])

    def tearDown(self):
        self.conn.close()

    def query(self, name):
        cursor = self.conn.execute((ROOT / "sql" / name).read_text(encoding="utf-8"))
        return [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]

    def test_multi_item_order_is_counted_once_and_canceled_excluded(self):
        rows = {row["month"]: row for row in self.query("02_monthly_orders.sql")}
        self.assertEqual(rows["2017-11"]["delivered_orders"], 2)
        self.assertEqual(rows["2017-11"]["merchandise_brl"], 35.0)
        self.assertEqual(rows["2017-12"]["delivered_orders"], 1)
        self.assertEqual(rows["2017-12"]["merchandise_brl"], 40.0)
        self.assertEqual(rows["2017-12"]["order_change"], -1)

    def test_states_reconcile_and_missing_category_is_preserved(self):
        states = self.query("03_state_comparison.sql")
        self.assertEqual(sum(row["nov_orders"] for row in states), 2)
        self.assertEqual(sum(row["dec_orders"] for row in states), 1)
        categories = self.query("05_category_comparison.sql")
        self.assertEqual(sum(round(row["nov_merchandise_brl"] * 100) for row in categories), 3500)
        self.assertIn("Unclassified", {row["category"] for row in categories})

    def test_daily_spine_matches_order_counts(self):
        days = {row["day"]: row for row in self.query("07_daily_orders.sql")}
        self.assertEqual(len(days), 61)
        self.assertEqual(days["2017-11-02"]["delivered_orders"], 1)
        self.assertEqual(sum(row["delivered_orders"] for day, row in days.items() if day.startswith("2017-11")), 2)


if __name__ == "__main__":
    unittest.main()
