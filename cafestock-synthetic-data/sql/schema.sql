-- PostgreSQL 18; run in an empty dedicated database. No destructive DDL.
BEGIN;
CREATE TABLE branches (
    branch_id bigint PRIMARY KEY,
    business_name text NOT NULL,
    branch_name text NOT NULL,
    timezone text NOT NULL,
    UNIQUE (branch_name)
);
CREATE TABLE categories (
    category_id bigint PRIMARY KEY,
    category_name text NOT NULL,
    UNIQUE (category_name)
);
CREATE TABLE suppliers (
    supplier_id bigint PRIMARY KEY,
    supplier_name text NOT NULL,
    lead_time_days integer NOT NULL,
    CHECK (lead_time_days > 0)
);
CREATE TABLE ingredients (
    ingredient_id bigint PRIMARY KEY,
    ingredient_name text NOT NULL,
    unit text NOT NULL,
    shelf_life_days integer NOT NULL,
    unit_cost_usd numeric(20,6) NOT NULL,
    package_size numeric(20,6) NOT NULL,
    minimum_order_qty numeric(20,6) NOT NULL,
    supplier_id bigint NOT NULL REFERENCES suppliers(supplier_id) ON DELETE RESTRICT,
    UNIQUE (ingredient_name),
    CHECK (shelf_life_days > 0),
    CHECK (unit_cost_usd >= 0),
    CHECK (package_size > 0),
    CHECK (minimum_order_qty > 0),
    CHECK (unit IN ('g','ml','piece'))
);
CREATE INDEX ON ingredients (supplier_id);
CREATE TABLE products (
    product_id bigint PRIMARY KEY,
    product_name text NOT NULL,
    category_id bigint NOT NULL REFERENCES categories(category_id) ON DELETE RESTRICT,
    source_product_type_proxy text NOT NULL,
    UNIQUE (product_name)
);
CREATE INDEX ON products (category_id);
CREATE TABLE recipes (
    recipe_id bigint PRIMARY KEY,
    product_id bigint NOT NULL REFERENCES products(product_id) ON DELETE RESTRICT,
    version text NOT NULL,
    UNIQUE (product_id)
);
CREATE TABLE recipe_ingredients (
    recipe_ingredient_id bigint PRIMARY KEY,
    recipe_id bigint NOT NULL REFERENCES recipes(recipe_id) ON DELETE RESTRICT,
    ingredient_id bigint NOT NULL REFERENCES ingredients(ingredient_id) ON DELETE RESTRICT,
    quantity numeric(20,6) NOT NULL,
    UNIQUE (recipe_id, ingredient_id),
    CHECK (quantity > 0)
);
CREATE INDEX ON recipe_ingredients (ingredient_id);
CREATE TABLE market_trends (
    trend_id bigint PRIMARY KEY,
    category_id bigint NOT NULL REFERENCES categories(category_id) ON DELETE RESTRICT,
    week_start date NOT NULL,
    available_at timestamptz NOT NULL,
    interest_index numeric(20,6) NOT NULL,
    provenance text NOT NULL,
    UNIQUE (category_id, week_start),
    CHECK (interest_index BETWEEN 0 AND 100)
);
CREATE TABLE latent_demand (
    demand_id bigint PRIMARY KEY,
    branch_id bigint NOT NULL REFERENCES branches(branch_id) ON DELETE RESTRICT,
    product_id bigint NOT NULL REFERENCES products(product_id) ON DELETE RESTRICT,
    transaction_at timestamptz NOT NULL,
    requested_qty integer NOT NULL,
    unit_price_usd numeric(20,6) NOT NULL,
    CHECK (requested_qty >= 0),
    CHECK (unit_price_usd >= 0)
);
CREATE INDEX ON latent_demand (branch_id);
CREATE INDEX ON latent_demand (product_id);
CREATE TABLE transactions (
    transaction_id bigint PRIMARY KEY,
    branch_id bigint NOT NULL REFERENCES branches(branch_id) ON DELETE RESTRICT,
    transaction_at timestamptz NOT NULL
);
CREATE TABLE transaction_items (
    transaction_item_id bigint PRIMARY KEY,
    transaction_id bigint NOT NULL REFERENCES transactions(transaction_id) ON DELETE RESTRICT,
    demand_id bigint NOT NULL REFERENCES latent_demand(demand_id) ON DELETE RESTRICT,
    product_id bigint NOT NULL REFERENCES products(product_id) ON DELETE RESTRICT,
    requested_qty integer NOT NULL,
    fulfilled_qty integer NOT NULL,
    unit_price_usd numeric(20,6) NOT NULL,
    UNIQUE (demand_id),
    CHECK (requested_qty >= 0),
    CHECK (fulfilled_qty >= 0),
    CHECK (unit_price_usd >= 0),
    CHECK (fulfilled_qty <= requested_qty)
);
CREATE INDEX ON transaction_items (transaction_id);
CREATE INDEX ON transaction_items (product_id);
CREATE TABLE customer_reviews (
    review_id bigint PRIMARY KEY,
    transaction_item_id bigint NOT NULL REFERENCES transaction_items(transaction_item_id) ON DELETE RESTRICT,
    review_at timestamptz NOT NULL,
    rating integer NOT NULL,
    review_text text NOT NULL,
    sentiment_label text NOT NULL,
    label_provenance text NOT NULL,
    CHECK (rating BETWEEN 1 AND 5),
    CHECK (sentiment_label IN ('positive','neutral','negative','mixed'))
);
CREATE INDEX ON customer_reviews (transaction_item_id);
CREATE TABLE review_aspects (
    review_aspect_id bigint PRIMARY KEY,
    review_id bigint NOT NULL REFERENCES customer_reviews(review_id) ON DELETE RESTRICT,
    aspect text NOT NULL,
    sentiment_label text NOT NULL,
    UNIQUE (review_id, aspect),
    CHECK (sentiment_label IN ('positive','neutral','negative','mixed'))
);
CREATE TABLE purchase_orders (
    purchase_order_id bigint PRIMARY KEY,
    branch_id bigint NOT NULL REFERENCES branches(branch_id) ON DELETE RESTRICT,
    supplier_id bigint NOT NULL REFERENCES suppliers(supplier_id) ON DELETE RESTRICT,
    ordered_at timestamptz NOT NULL,
    expected_delivery_at timestamptz NOT NULL,
    delivered_at timestamptz,
    status text NOT NULL,
    CHECK (status IN ('open','delivered')),
    CHECK (expected_delivery_at > ordered_at),
    CHECK ((status = 'open' AND delivered_at IS NULL) OR (status = 'delivered' AND delivered_at IS NOT NULL))
);
CREATE INDEX ON purchase_orders (branch_id);
CREATE INDEX ON purchase_orders (supplier_id);
CREATE TABLE purchase_order_items (
    purchase_order_item_id bigint PRIMARY KEY,
    purchase_order_id bigint NOT NULL REFERENCES purchase_orders(purchase_order_id) ON DELETE RESTRICT,
    ingredient_id bigint NOT NULL REFERENCES ingredients(ingredient_id) ON DELETE RESTRICT,
    quantity numeric(20,6) NOT NULL,
    unit_cost_usd numeric(20,6) NOT NULL,
    CHECK (quantity > 0),
    CHECK (unit_cost_usd >= 0)
);
CREATE INDEX ON purchase_order_items (purchase_order_id);
CREATE INDEX ON purchase_order_items (ingredient_id);
CREATE TABLE inventory_movements (
    movement_id bigint PRIMARY KEY,
    branch_id bigint NOT NULL REFERENCES branches(branch_id) ON DELETE RESTRICT,
    ingredient_id bigint NOT NULL REFERENCES ingredients(ingredient_id) ON DELETE RESTRICT,
    movement_at timestamptz NOT NULL,
    movement_type text NOT NULL,
    quantity numeric(20,6) NOT NULL,
    transaction_item_id bigint REFERENCES transaction_items(transaction_item_id) ON DELETE RESTRICT,
    purchase_order_item_id bigint REFERENCES purchase_order_items(purchase_order_item_id) ON DELETE RESTRICT
);
CREATE INDEX ON inventory_movements (ingredient_id);
CREATE INDEX ON inventory_movements (transaction_item_id);
CREATE INDEX ON inventory_movements (purchase_order_item_id);
CREATE TABLE inventory_snapshots (
    snapshot_id bigint PRIMARY KEY,
    branch_id bigint NOT NULL REFERENCES branches(branch_id) ON DELETE RESTRICT,
    ingredient_id bigint NOT NULL REFERENCES ingredients(ingredient_id) ON DELETE RESTRICT,
    date date NOT NULL,
    opening_stock numeric(20,6) NOT NULL,
    receipts numeric(20,6) NOT NULL,
    consumption numeric(20,6) NOT NULL,
    waste numeric(20,6) NOT NULL,
    adjustments numeric(20,6) NOT NULL,
    closing_stock numeric(20,6) NOT NULL,
    UNIQUE (branch_id, ingredient_id, date),
    CHECK (opening_stock >= 0),
    CHECK (receipts >= 0),
    CHECK (consumption >= 0),
    CHECK (waste >= 0),
    CHECK (closing_stock >= 0),
    CHECK (abs(closing_stock - (opening_stock + receipts - consumption - waste + adjustments)) < 0.00001)
);
CREATE INDEX ON inventory_snapshots (ingredient_id);
CREATE TABLE stockout_events (
    stockout_event_id bigint PRIMARY KEY,
    transaction_item_id bigint NOT NULL REFERENCES transaction_items(transaction_item_id) ON DELETE RESTRICT,
    ingredient_id bigint NOT NULL REFERENCES ingredients(ingredient_id) ON DELETE RESTRICT,
    event_at timestamptz NOT NULL,
    shortage_qty numeric(20,6) NOT NULL,
    unfulfilled_product_qty integer NOT NULL,
    CHECK (shortage_qty >= 0)
);
CREATE INDEX ON stockout_events (transaction_item_id);
CREATE INDEX ON stockout_events (ingredient_id);
CREATE TABLE waste_records (
    waste_id bigint PRIMARY KEY,
    movement_id bigint NOT NULL REFERENCES inventory_movements(movement_id) ON DELETE RESTRICT,
    reason text NOT NULL,
    quantity numeric(20,6) NOT NULL,
    CHECK (quantity > 0)
);
CREATE INDEX ON waste_records (movement_id);
CREATE TABLE restock_decision_dataset (
    decision_id bigint PRIMARY KEY,
    branch_id bigint NOT NULL REFERENCES branches(branch_id) ON DELETE RESTRICT,
    ingredient_id bigint NOT NULL REFERENCES ingredients(ingredient_id) ON DELETE RESTRICT,
    decision_at timestamptz NOT NULL,
    history_days integer NOT NULL,
    mean_daily_consumption_14d numeric(20,6) NOT NULL,
    on_hand numeric(20,6) NOT NULL,
    on_order numeric(20,6) NOT NULL,
    lead_time_days integer NOT NULL,
    shelf_life_days integer NOT NULL,
    package_size numeric(20,6) NOT NULL,
    minimum_order_qty numeric(20,6) NOT NULL,
    baseline_purchase_qty numeric(20,6) NOT NULL,
    market_interest_latest numeric(20,6) NOT NULL,
    market_feature_max_at timestamptz NOT NULL,
    review_count_14d integer NOT NULL,
    sentiment_mean_14d numeric(20,6) NOT NULL,
    sentiment_feature_max_at timestamptz,
    label_window_end timestamptz NOT NULL,
    future_stockout_7d integer,
    label_observed integer NOT NULL,
    split text NOT NULL,
    UNIQUE (branch_id, ingredient_id, decision_at),
    CHECK (on_hand >= 0),
    CHECK (on_order >= 0),
    CHECK (lead_time_days > 0),
    CHECK (shelf_life_days > 0),
    CHECK (package_size > 0),
    CHECK (minimum_order_qty > 0),
    CHECK (baseline_purchase_qty >= 0)
);
CREATE INDEX ON restock_decision_dataset (ingredient_id);
CREATE TABLE inventory_risk_ml_dataset (
    risk_row_id bigint PRIMARY KEY,
    branch_id bigint NOT NULL REFERENCES branches(branch_id) ON DELETE RESTRICT,
    ingredient_id bigint NOT NULL REFERENCES ingredients(ingredient_id) ON DELETE RESTRICT,
    decision_at timestamptz NOT NULL,
    history_days integer NOT NULL,
    mean_daily_consumption_14d numeric(20,6) NOT NULL,
    on_hand numeric(20,6) NOT NULL,
    on_order numeric(20,6) NOT NULL,
    lead_time_days integer NOT NULL,
    shelf_life_days integer NOT NULL,
    package_size numeric(20,6) NOT NULL,
    minimum_order_qty numeric(20,6) NOT NULL,
    baseline_purchase_qty numeric(20,6) NOT NULL,
    market_interest_latest numeric(20,6) NOT NULL,
    market_feature_max_at timestamptz NOT NULL,
    review_count_14d integer NOT NULL,
    sentiment_mean_14d numeric(20,6) NOT NULL,
    sentiment_feature_max_at timestamptz,
    label_window_end timestamptz NOT NULL,
    target_stockout integer,
    label_observed integer NOT NULL,
    split text NOT NULL,
    risk_label text,
    CHECK (on_hand >= 0),
    CHECK (on_order >= 0),
    CHECK (lead_time_days > 0),
    CHECK (shelf_life_days > 0),
    CHECK (package_size > 0),
    CHECK (minimum_order_qty > 0),
    CHECK (baseline_purchase_qty >= 0)
);
CREATE INDEX ON inventory_risk_ml_dataset (branch_id);
CREATE INDEX ON inventory_risk_ml_dataset (ingredient_id);
CREATE TABLE sentiment_ml_dataset (
    sentiment_row_id bigint PRIMARY KEY,
    review_id bigint NOT NULL REFERENCES customer_reviews(review_id) ON DELETE RESTRICT,
    review_text text NOT NULL,
    sentiment_label text NOT NULL,
    rating integer NOT NULL,
    review_at timestamptz NOT NULL,
    split text NOT NULL,
    CHECK (sentiment_label IN ('positive','neutral','negative','mixed'))
);
CREATE INDEX ON sentiment_ml_dataset (review_id);
CREATE TABLE trend_ml_dataset (
    trend_row_id bigint PRIMARY KEY,
    category_id bigint NOT NULL REFERENCES categories(category_id) ON DELETE RESTRICT,
    decision_at timestamptz NOT NULL,
    interest_lag_1w numeric(20,6) NOT NULL,
    feature_max_at timestamptz,
    target_fulfilled_units_next_7d integer,
    label_observed integer NOT NULL,
    split text NOT NULL
);
CREATE INDEX ON trend_ml_dataset (category_id);
CREATE INDEX ON transactions (branch_id, transaction_at);
CREATE INDEX ON inventory_movements (branch_id, ingredient_id, movement_at);
CREATE INDEX ON customer_reviews (review_at);
COMMIT;
