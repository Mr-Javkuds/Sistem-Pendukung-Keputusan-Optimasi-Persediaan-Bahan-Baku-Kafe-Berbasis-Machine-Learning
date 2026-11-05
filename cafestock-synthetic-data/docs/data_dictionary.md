# Data dictionary

All output rows are synthetic; input/ contains preserved external observations. Money is IDR; quantities use ingredients.unit (g, ml, piece); timestamps use Asia/Jakarta (+07:00). Empty CSV cells import as SQL NULL. IDs are stable application-assigned bigint keys.

## regions

| Field | PostgreSQL type | Meaning |
|---|---|---|
| region_id | bigint | Region id; primary key |
| region_name | text | Region name |
| city | text | City |
| region_level | text | Region level |

## branches

| Field | PostgreSQL type | Meaning |
|---|---|---|
| branch_id | bigint | Branch id; primary key |
| business_name | text | Business name |
| branch_name | text | Branch name |
| region_id | bigint | Region id; FK to regions |
| timezone | text | Timezone |
| source_location_proxy | text | Explicit unrelated source location used only to transfer transaction patterns |

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
| unit_cost_idr | numeric(20,6) | IDR per ingredient base unit; invented local cost, not an FX conversion |
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
| base_price_idr | numeric(20,6) | Base price idr |

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
| region_id | bigint | Region id; FK to regions |
| category_id | bigint | Category id; FK to categories |
| week_start | date | Week start |
| available_at | timestamptz | Available at |
| interest_index | numeric(20,6) | Interest index |
| provenance | text | Provenance |

## social_posts

| Field | PostgreSQL type | Meaning |
|---|---|---|
| post_id | bigint | Post id; primary key |
| platform | text | Platform |
| source_post_key | text | Source post key |
| source_url | text | NULL for synthetic content; no real Instagram link is claimed; nullable |
| content_text | text | Original synthetic Indonesian discussion about a menu, not a cafe review |
| published_at | timestamptz | Published at |
| collected_at | timestamptz | Simulated monthly ingestion time; later than publication; gates feature availability |
| batch_key | text | Batch key |
| region_id | bigint | Region id; FK to regions; nullable |
| location_evidence | text | synthetic_scenario for assigned market or unknown; never inferred from account location |
| language | text | Language |
| provenance | text | Provenance |

## menu_mentions

| Field | PostgreSQL type | Meaning |
|---|---|---|
| mention_id | bigint | Mention id; primary key |
| post_id | bigint | Post id; FK to social_posts |
| product_id | bigint | Product id; FK to products |
| sentiment_label | text | Sentiment label |
| label_provenance | text | Label provenance |

## menu_aspects

| Field | PostgreSQL type | Meaning |
|---|---|---|
| menu_aspect_id | bigint | Menu aspect id; primary key |
| mention_id | bigint | Mention id; FK to menu_mentions |
| aspect | text | Aspect |
| sentiment_label | text | Sentiment label |

## menu_market_signals

| Field | PostgreSQL type | Meaning |
|---|---|---|
| signal_id | bigint | Signal id; primary key |
| region_id | bigint | Region id; FK to regions |
| product_id | bigint | Product id; FK to products |
| period_start | date | Period start |
| available_at | timestamptz | Available at |
| source_max_published_at | timestamptz | Source max published at |
| post_count | integer | Post count |
| positive_count | integer | Positive count |
| neutral_count | integer | Neutral count |
| negative_count | integer | Negative count |
| mixed_count | integer | Mixed count |
| sentiment_mean | numeric(20,6) | Sentiment mean |
| provenance | text | Provenance |

## latent_demand

| Field | PostgreSQL type | Meaning |
|---|---|---|
| demand_id | bigint | Demand id; primary key |
| branch_id | bigint | Branch id; FK to branches |
| product_id | bigint | Product id; FK to products |
| transaction_at | timestamptz | Transaction at |
| requested_qty | integer | Simulated latent product units requested |
| unit_price_idr | numeric(20,6) | Unit price idr |

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
| unit_price_idr | numeric(20,6) | Unit price idr |

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
| unit_cost_idr | numeric(20,6) | IDR per ingredient base unit; invented local cost, not an FX conversion |

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
| market_interest_lag_1w | numeric(20,6) | Market interest lag 1w |
| market_feature_max_at | timestamptz | Latest source timestamp of historical synthetic weekly interest feature |
| social_post_count_latest_month | integer | Count of available menu discussions for linked products in city plus branch district |
| menu_sentiment_latest_month | numeric(20,6) | Mean menu opinion: positive=1, negative=-1, neutral/mixed=0; missing flagged separately |
| social_feature_max_at | timestamptz | Latest publication time used in the historical menu sentiment feature; nullable |
| social_available_at | timestamptz | Latest actual synthetic monthly collection time contributing to features; nullable |
| social_period_start | date | Publication month represented in latest available regional menu signals; nullable |
| social_data_available | integer | 0 means no eligible collected batch; score 0 must not be interpreted as observed neutrality |
| social_age_days | integer | Days since contributing monthly batch availability; 0 with availability flag 0 means missing |
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
| market_interest_lag_1w | numeric(20,6) | Market interest lag 1w |
| market_feature_max_at | timestamptz | Latest source timestamp of historical synthetic weekly interest feature |
| social_post_count_latest_month | integer | Count of available menu discussions for linked products in city plus branch district |
| menu_sentiment_latest_month | numeric(20,6) | Mean menu opinion: positive=1, negative=-1, neutral/mixed=0; missing flagged separately |
| social_feature_max_at | timestamptz | Latest publication time used in the historical menu sentiment feature; nullable |
| social_available_at | timestamptz | Latest actual synthetic monthly collection time contributing to features; nullable |
| social_period_start | date | Publication month represented in latest available regional menu signals; nullable |
| social_data_available | integer | 0 means no eligible collected batch; score 0 must not be interpreted as observed neutrality |
| social_age_days | integer | Days since contributing monthly batch availability; 0 with availability flag 0 means missing |
| label_window_end | timestamptz | Label window end |
| target_stockout | integer | Same evaluation outcome as restock table; excluded from features; nullable |
| label_observed | integer | 1 if complete future outcome window is available, otherwise 0 |
| split | text | Chronological train/validation/test; boundary label rows are purged from training |
| risk_label | text | Risk label; nullable |

## sentiment_ml_dataset

| Field | PostgreSQL type | Meaning |
|---|---|---|
| sentiment_row_id | bigint | Sentiment row id; primary key |
| mention_id | bigint | Mention id; FK to menu_mentions |
| post_id | bigint | Post id; FK to social_posts |
| product_id | bigint | Product id; FK to products |
| region_id | bigint | Region id; FK to regions; nullable |
| published_at | timestamptz | Published at |
| collected_at | timestamptz | Simulated monthly ingestion time; later than publication; gates feature availability |
| content_text | text | Original synthetic Indonesian discussion about a menu, not a cafe review |
| sentiment_label | text | Sentiment label |
| label_provenance | text | Label provenance |
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
