-- A calendar spine preserves zero-order dates. These are purchase dates, not
-- delivery dates; only orders whose recorded final status is delivered count.
WITH RECURSIVE calendar(day) AS (
  SELECT '2017-11-01'
  UNION ALL
  SELECT date(day, '+1 day') FROM calendar WHERE day < '2017-12-31'
), daily AS (
  SELECT substr(purchased_at, 1, 10) AS day,
         COUNT(*) AS delivered_orders,
         SUM(item_value_cents) AS merchandise_cents
  FROM delivered_orders
  WHERE purchased_at >= '2017-11-01' AND purchased_at < '2018-01-01'
  GROUP BY substr(purchased_at, 1, 10)
)
SELECT calendar.day, COALESCE(daily.delivered_orders, 0) AS delivered_orders,
       ROUND(COALESCE(daily.merchandise_cents, 0) / 100.0, 2) AS merchandise_brl
FROM calendar LEFT JOIN daily ON daily.day = calendar.day
ORDER BY calendar.day;
