-- Structural, relationship and population checks. A count > 0 is described in
-- the analysis notes; zero is not assumed for legitimate missing categories.
SELECT 'orders' AS check_name, COUNT(*) AS result FROM orders
UNION ALL SELECT 'customers', COUNT(*) FROM customers
UNION ALL SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'delivered_orders_all_periods', COUNT(*) FROM delivered_orders
UNION ALL SELECT 'orders_missing_customer', COUNT(*) FROM orders o LEFT JOIN customers c ON c.customer_id=o.customer_id WHERE c.customer_id IS NULL
UNION ALL SELECT 'items_missing_order', COUNT(*) FROM order_items i LEFT JOIN orders o ON o.order_id=i.order_id WHERE o.order_id IS NULL
UNION ALL SELECT 'items_missing_product', COUNT(*) FROM order_items i LEFT JOIN products p ON p.product_id=i.product_id WHERE p.product_id IS NULL
UNION ALL SELECT 'delivered_orders_without_items', COUNT(*) FROM delivered_orders WHERE item_count=0
UNION ALL SELECT 'delivered_item_rows_without_category', COUNT(*) FROM delivered_order_items WHERE category='Unclassified';
