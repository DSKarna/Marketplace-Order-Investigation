-- SQLite schema. Grain is explicit: orders = one row per order;
-- order_items = one row per item within an order. Prices are integer cents.
CREATE TABLE orders (
  order_id TEXT PRIMARY KEY,
  customer_id TEXT NOT NULL,
  order_status TEXT NOT NULL,
  purchased_at TEXT NOT NULL,
  approved_at TEXT,
  carrier_at TEXT,
  delivered_at TEXT,
  estimated_delivery_at TEXT
);
CREATE TABLE customers (
  customer_id TEXT PRIMARY KEY,
  customer_unique_id TEXT,
  zip_prefix TEXT,
  city TEXT,
  state TEXT
);
CREATE TABLE order_items (
  order_id TEXT NOT NULL,
  order_item_id INTEGER NOT NULL,
  product_id TEXT NOT NULL,
  seller_id TEXT,
  shipping_limit_at TEXT,
  price_cents INTEGER NOT NULL,
  freight_cents INTEGER NOT NULL,
  PRIMARY KEY (order_id, order_item_id)
);
CREATE TABLE products (
  product_id TEXT PRIMARY KEY,
  category_pt TEXT
);
CREATE TABLE category_translation (
  category_pt TEXT PRIMARY KEY,
  category_en TEXT
);

CREATE INDEX idx_orders_status_date ON orders(order_status, purchased_at);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_items_order ON order_items(order_id);
CREATE INDEX idx_items_product ON order_items(product_id);

-- Aggregate item value BEFORE joining to the order table. This prevents an
-- order with multiple items from being counted multiple times.
CREATE VIEW item_value_by_order AS
SELECT order_id, SUM(price_cents) AS item_value_cents, COUNT(*) AS item_count
FROM order_items
GROUP BY order_id;

CREATE VIEW delivered_orders AS
SELECT o.order_id, o.customer_id, o.purchased_at,
       COALESCE(NULLIF(c.city, ''), 'Unknown') AS city,
       COALESCE(NULLIF(c.state, ''), 'Unknown') AS state,
       COALESCE(i.item_value_cents, 0) AS item_value_cents,
       COALESCE(i.item_count, 0) AS item_count
FROM orders o
LEFT JOIN customers c ON c.customer_id = o.customer_id
LEFT JOIN item_value_by_order i ON i.order_id = o.order_id
WHERE o.order_status = 'delivered';

-- Item-grain view for additive product-category sales. A multi-category order
-- can appear in several categories, so do not add category order counts.
CREATE VIEW delivered_order_items AS
SELECT o.order_id, o.purchased_at,
       COALESCE(NULLIF(c.state, ''), 'Unknown') AS state,
       COALESCE(NULLIF(t.category_en, ''), NULLIF(p.category_pt, ''), 'Unclassified') AS category,
       i.order_item_id, i.price_cents
FROM orders o
JOIN order_items i ON i.order_id = o.order_id
LEFT JOIN customers c ON c.customer_id = o.customer_id
LEFT JOIN products p ON p.product_id = i.product_id
LEFT JOIN category_translation t ON t.category_pt = p.category_pt
WHERE o.order_status = 'delivered';
