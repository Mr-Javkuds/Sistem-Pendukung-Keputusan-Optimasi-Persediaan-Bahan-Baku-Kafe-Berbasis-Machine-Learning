# Data dictionary

All output rows are synthetic; input/ contains preserved external observations. Money is USD; quantities use ingredients.unit (g, ml, piece); timestamps include NYC UTC offset. Empty CSV cells import as SQL NULL. IDs are stable application-assigned bigint keys.

## branches

| Field | PostgreSQL type | Meaning |
|---|---|---|
| branch_id | bigint | Branch id; primary key |
| business_name | text | Business name |
| branch_name | text | Branch name |
| timezone | text | Timezone |

## categories

| Field | PostgreSQL type | Meaning |
|---|---|---|
| category_id | bigint | Category id; primary key |
| category_name | text | Category name |

## suppliers

| Field | PostgreSQL type | Meaning |
|---|---|---|
| supplier_id | bigint | Supplier id; primary key |
| supplier_name | text | Supplier name |
| lead_time_days | integer | Lead time days |

## ingredients

| Field | PostgreSQL type | Meaning |
|---|---|---|
| ingredient_id | bigint | Ingredient id; primary key |
| ingredient_name | text | Ingredient name |
| unit | text | Unit |
| shelf_life_days | integer | Shelf life days |
| unit_cost_usd | numeric(20,6) | USD per ingredient base unit |
| package_size | numeric(20,6) | Purchase-package quantity in ingredient base units |
| minimum_order_qty | numeric(20,6) | Minimum purchase units, a package multiple |
| supplier_id | bigint | Supplier id; FK to suppliers |

## products

| Field | PostgreSQL type | Meaning |
|---|---|---|
| product_id | bigint | Product id; primary key |
| product_name | text | Product name |
| category_id | bigint | Category id; FK to categories |
| source_product_type_proxy | text | Explicit source type used for statistical sampling; not source identity |

## recipes

| Field | PostgreSQL type | Meaning |
|---|---|---|
| recipe_id | bigint | Recipe id; primary key |
| product_id | bigint | Product id; FK to products |
| version | text | Version |

## recipe_ingredients

| Field | PostgreSQL type | Meaning |
|---|---|---|
| recipe_ingredient_id | bigint | Recipe ingredient id; primary key |
| recipe_id | bigint | Recipe id; FK to recipes |
| ingredient_id | bigint | Ingredient id; FK to ingredients |
| quantity | numeric(20,6) | Ingredient base units; signed delta only in inventory_movements |

## market_trends

| Field | PostgreSQL type | Meaning |
|---|---|---|
| trend_id | bigint | Trend id; primary key |
| category_id | bigint | Category id; FK to categories |
| week_start | date | Week start |
| available_at | timestamptz | Available at |
| interest_index | numeric(20,6) | Interest index |
| provenance | text | Provenance |

## latent_demand

| Field | PostgreSQL type | Meaning |
|---|---|---|
| demand_id | bigint | Demand id; primary key |
| branch_id | bigint | Branch id; FK to branches |
| product_id | bigint | Product id; FK to products |
| transaction_at | timestamptz | Transaction at |
| requested_qty | integer | Simulated latent product units requested |
| unit_price_usd | numeric(20,6) | Unit price usd |

## transactions

| Field | PostgreSQL type | Meaning |
|---|---|---|
| transaction_id | bigint | Transaction id; primary key |
| branch_id | bigint | Branch id; FK to branches |
| transaction_at | timestamptz | Transaction at |

## transaction_items

| Field | PostgreSQL type | Meaning |
|---|---|---|
| transaction_item_id | bigint | Transaction item id; primary key |
| transaction_id | bigint | Transaction id; FK to transactions |
| demand_id | bigint | Demand id; FK to latent_demand |
| product_id | bigint | Product id; FK to products |
| requested_qty | integer | Simulated latent product units requested |
| fulfilled_qty | integer | Product units actually fulfilled and consuming recipe ingredients |
| unit_price_usd | numeric(20,6) | Unit price usd |

## customer_reviews

| Field | PostgreSQL type | Meaning |
|---|---|---|
| review_id | bigint | Review id; primary key |
| transaction_item_id | bigint | Transaction item id; FK to transaction_items |
| review_at | timestamptz | Review at |
| rating | integer | Rating |
| review_text | text | Review text |
| sentiment_label | text | Sentiment label |
| label_provenance | text | Label provenance |

## review_aspects

| Field | PostgreSQL type | Meaning |
|---|---|---|
| review_aspect_id | bigint | Review aspect id; primary key |
| review_id | bigint | Review id; FK to customer_reviews |
| aspect | text | Aspect |
| sentiment_label | text | Sentiment label |

## purchase_orders

| Field | PostgreSQL type | Meaning |
|---|---|---|
| purchase_order_id | bigint | Purchase order id; primary key |
| branch_id | bigint | Branch id; FK to branches |
| supplier_id | bigint | Supplier id; FK to suppliers |
| ordered_at | timestamptz | Ordered at |
| expected_delivery_at | timestamptz | Expected delivery at |
| delivered_at | timestamptz | Delivered at; nullable |
| status | text | Status |

## purchase_order_items

| Field | PostgreSQL type | Meaning |
|---|---|---|
| purchase_order_item_id | bigint | Purchase order item id; primary key |
| purchase_order_id | bigint | Purchase order id; FK to purchase_orders |
| ingredient_id | bigint | Ingredient id; FK to ingredients |
| quantity | numeric(20,6) | Ingredient base units; signed delta only in inventory_movements |
| unit_cost_usd | numeric(20,6) | USD per ingredient base unit |

## inventory_movements

| Field | PostgreSQL type | Meaning |
|---|---|---|
| movement_id | bigint | Movement id; primary key |
| branch_id | bigint | Branch id; FK to branches |
| ingredient_id | bigint | Ingredient id; FK to ingredients |
| movement_at | timestamptz | Movement at |
| movement_type | text | Movement type |
| quantity | numeric(20,6) | Ingredient base units; signed delta only in inventory_movements |
| transaction_item_id | bigint | Transaction item id; FK to transaction_items; nullable |
| purchase_order_item_id | bigint | Purchase order item id; FK to purchase_order_items; nullable |

## inventory_snapshots

| Field | PostgreSQL type | Meaning |
|---|---|---|
| snapshot_id | bigint | Snapshot id; primary key |
| branch_id | bigint | Branch id; FK to branches |
| ingredient_id | bigint | Ingredient id; FK to ingredients |
| date | date | Date |
| opening_stock | numeric(20,6) | Opening stock |
| receipts | numeric(20,6) | Receipts |
| consumption | numeric(20,6) | Consumption |
| waste | numeric(20,6) | Waste |
| adjustments | numeric(20,6) | Adjustments |
| closing_stock | numeric(20,6) | Closing stock |

## stockout_events

| Field | PostgreSQL type | Meaning |
|---|---|---|
| stockout_event_id | bigint | Stockout event id; primary key |
| transaction_item_id | bigint | Transaction item id; FK to transaction_items |
| ingredient_id | bigint | Ingredient id; FK to ingredients |
| event_at | timestamptz | Event at |
| shortage_qty | numeric(20,6) | Ingredient units short before fulfilling the requested product |
| unfulfilled_product_qty | integer | Unfulfilled product qty |

## waste_records

| Field | PostgreSQL type | Meaning |
|---|---|---|
| waste_id | bigint | Waste id; primary key |
| movement_id | bigint | Movement id; FK to inventory_movements |
| reason | text | Reason |
| quantity | numeric(20,6) | Ingredient base units; signed delta only in inventory_movements |

## restock_decision_dataset

| Field | PostgreSQL type | Meaning |
|---|---|---|
| decision_id | bigint | Decision id; primary key |
| branch_id | bigint | Branch id; FK to branches |
| ingredient_id | bigint | Ingredient id; FK to ingredients |
| decision_at | timestamptz | Decision at |
| history_days | integer | Number of completed days used, capped at 14; zero uses engineering prior |
| mean_daily_consumption_14d | numeric(20,6) | Prior completed-day mean ingredient consumption in base units/day |
| on_hand | numeric(20,6) | Usable base units at 05:00 after expiry, adjustments and receipts |
| on_order | numeric(20,6) | Outstanding units before this decision order |
| lead_time_days | integer | Lead time days |
| shelf_life_days | integer | Shelf life days |
| package_size | numeric(20,6) | Purchase-package quantity in ingredient base units |
| minimum_order_qty | numeric(20,6) | Minimum purchase units, a package multiple |
| baseline_purchase_qty | numeric(20,6) | Reference policy quantity in base units; not mathematically optimal |
| market_interest_latest | numeric(20,6) | Equal mean of latest known category indices associated via recipes |
| market_feature_max_at | timestamptz | Latest source timestamp of historical synthetic weekly interest feature |
| review_count_14d | integer | Review count 14d |
| sentiment_mean_14d | numeric(20,6) | Branch prior 14-day mean rule sentiment; mixed and neutral score 0 |
| sentiment_feature_max_at | timestamptz | Latest review timestamp used; NULL means no prior review; nullable |
| label_window_end | timestamptz | Label window end |
| future_stockout_7d | integer | Evaluation target: shortage event in configured horizon; NULL if censored; nullable |
| label_observed | integer | 1 if complete future outcome window is available, otherwise 0 |
| split | text | Chronological train/validation/test; boundary label rows are purged from training |

## inventory_risk_ml_dataset

| Field | PostgreSQL type | Meaning |
|---|---|---|
| risk_row_id | bigint | Risk row id; primary key |
| branch_id | bigint | Branch id; FK to branches |
| ingredient_id | bigint | Ingredient id; FK to ingredients |
| decision_at | timestamptz | Decision at |
| history_days | integer | Number of completed days used, capped at 14; zero uses engineering prior |
| mean_daily_consumption_14d | numeric(20,6) | Prior completed-day mean ingredient consumption in base units/day |
| on_hand | numeric(20,6) | Usable base units at 05:00 after expiry, adjustments and receipts |
| on_order | numeric(20,6) | Outstanding units before this decision order |
| lead_time_days | integer | Lead time days |
| shelf_life_days | integer | Shelf life days |
| package_size | numeric(20,6) | Purchase-package quantity in ingredient base units |
| minimum_order_qty | numeric(20,6) | Minimum purchase units, a package multiple |
| baseline_purchase_qty | numeric(20,6) | Reference policy quantity in base units; not mathematically optimal |
| market_interest_latest | numeric(20,6) | Equal mean of latest known category indices associated via recipes |
| market_feature_max_at | timestamptz | Latest source timestamp of historical synthetic weekly interest feature |
| review_count_14d | integer | Review count 14d |
| sentiment_mean_14d | numeric(20,6) | Branch prior 14-day mean rule sentiment; mixed and neutral score 0 |
| sentiment_feature_max_at | timestamptz | Latest review timestamp used; NULL means no prior review; nullable |
| label_window_end | timestamptz | Label window end |
| target_stockout | integer | Same evaluation outcome as restock table; excluded from features; nullable |
| label_observed | integer | 1 if complete future outcome window is available, otherwise 0 |
| split | text | Chronological train/validation/test; boundary label rows are purged from training |
| risk_label | text | Risk label; nullable |

## sentiment_ml_dataset

| Field | PostgreSQL type | Meaning |
|---|---|---|
| sentiment_row_id | bigint | Sentiment row id; primary key |
| review_id | bigint | Review id; FK to customer_reviews |
| review_text | text | Review text |
| sentiment_label | text | Sentiment label |
| rating | integer | Rating |
| review_at | timestamptz | Review at |
| split | text | Chronological train/validation/test; boundary label rows are purged from training |

## trend_ml_dataset

| Field | PostgreSQL type | Meaning |
|---|---|---|
| trend_row_id | bigint | Trend row id; primary key |
| category_id | bigint | Category id; FK to categories |
| decision_at | timestamptz | Decision at |
| interest_lag_1w | numeric(20,6) | Interest lag 1w |
| feature_max_at | timestamptz | Feature max at; nullable |
| target_fulfilled_units_next_7d | integer | Target fulfilled units next 7d; nullable |
| label_observed | integer | 1 if complete future outcome window is available, otherwise 0 |
| split | text | Chronological train/validation/test; boundary label rows are purged from training |
