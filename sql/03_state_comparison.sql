-- Net order changes add exactly to the marketplace-wide order change because
-- each order belongs to one customer state. Includes gains and losses.
WITH states AS (
  SELECT state,
         SUM(CASE WHEN purchased_at >= '2017-11-01' AND purchased_at < '2017-12-01' THEN 1 ELSE 0 END) AS nov_orders,
         SUM(CASE WHEN purchased_at >= '2017-12-01' AND purchased_at < '2018-01-01' THEN 1 ELSE 0 END) AS dec_orders
  FROM delivered_orders
  WHERE purchased_at >= '2017-11-01' AND purchased_at < '2018-01-01'
  GROUP BY state
)
SELECT state, nov_orders, dec_orders,
       dec_orders - nov_orders AS order_change,
       ROUND(1.0 * (dec_orders - nov_orders) / NULLIF(nov_orders, 0), 6) AS order_change_rate
FROM states
ORDER BY order_change ASC, state;
