-- Complete purchase months only. Item value excludes freight, taxes and
-- platform fees; it is marketplace merchandise value, not platform revenue.
WITH monthly AS (
  SELECT substr(purchased_at, 1, 7) AS month,
         COUNT(*) AS delivered_orders,
         SUM(item_value_cents) AS merchandise_cents
  FROM delivered_orders
  WHERE purchased_at >= '2017-01-01' AND purchased_at < '2018-08-01'
  GROUP BY substr(purchased_at, 1, 7)
), changes AS (
  SELECT month, delivered_orders, merchandise_cents,
         LAG(delivered_orders) OVER (ORDER BY month) AS previous_orders,
         LAG(merchandise_cents) OVER (ORDER BY month) AS previous_merchandise_cents
  FROM monthly
)
SELECT month, delivered_orders, previous_orders,
       delivered_orders - previous_orders AS order_change,
       ROUND(1.0 * (delivered_orders - previous_orders) / NULLIF(previous_orders, 0), 6) AS order_change_rate,
       ROUND(merchandise_cents / 100.0, 2) AS merchandise_brl,
       ROUND(previous_merchandise_cents / 100.0, 2) AS previous_merchandise_brl,
       ROUND((merchandise_cents - previous_merchandise_cents) / 100.0, 2) AS merchandise_change_brl,
       ROUND(1.0 * (merchandise_cents - previous_merchandise_cents) / NULLIF(previous_merchandise_cents, 0), 6) AS merchandise_change_rate
FROM changes
ORDER BY month;
