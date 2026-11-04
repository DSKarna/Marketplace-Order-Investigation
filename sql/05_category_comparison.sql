-- Compare item-level merchandise value, not order counts. Categories are
-- additive by item value even when one order spans multiple categories.
WITH categories AS (
  SELECT category,
         SUM(CASE WHEN purchased_at >= '2017-11-01' AND purchased_at < '2017-12-01' THEN price_cents ELSE 0 END) AS nov_cents,
         SUM(CASE WHEN purchased_at >= '2017-12-01' AND purchased_at < '2018-01-01' THEN price_cents ELSE 0 END) AS dec_cents
  FROM delivered_order_items
  WHERE purchased_at >= '2017-11-01' AND purchased_at < '2018-01-01'
  GROUP BY category
)
SELECT category,
       ROUND(nov_cents / 100.0, 2) AS nov_merchandise_brl,
       ROUND(dec_cents / 100.0, 2) AS dec_merchandise_brl,
       ROUND((dec_cents - nov_cents) / 100.0, 2) AS merchandise_change_brl,
       ROUND(1.0 * (dec_cents - nov_cents) / NULLIF(nov_cents, 0), 6) AS merchandise_change_rate
FROM categories
ORDER BY merchandise_change_brl ASC, category;
