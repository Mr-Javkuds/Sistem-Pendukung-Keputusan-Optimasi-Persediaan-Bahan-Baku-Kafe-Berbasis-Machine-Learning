# Validation report

374/374 checks passed.

| Check | Result | Detail |
|---|---|---|
| regions primary key | PASS |  |
| regions required region_id | PASS |  |
| regions required region_name | PASS |  |
| regions required city | PASS |  |
| regions required region_level | PASS |  |
| regions unique region_name,city | PASS |  |
| branches primary key | PASS |  |
| branches required branch_id | PASS |  |
| branches required business_name | PASS |  |
| branches required branch_name | PASS |  |
| branches required region_id | PASS |  |
| branches required timezone | PASS |  |
| branches required source_location_proxy | PASS |  |
| branches unique branch_name | PASS |  |
| branches FK region_id | PASS |  |
| categories primary key | PASS |  |
| categories required category_id | PASS |  |
| categories required category_name | PASS |  |
| categories unique category_name | PASS |  |
| suppliers primary key | PASS |  |
| suppliers required supplier_id | PASS |  |
| suppliers required supplier_name | PASS |  |
| suppliers required lead_time_days | PASS |  |
| ingredients primary key | PASS |  |
| ingredients required ingredient_id | PASS |  |
| ingredients required ingredient_name | PASS |  |
| ingredients required unit | PASS |  |
| ingredients required shelf_life_days | PASS |  |
| ingredients required unit_cost_idr | PASS |  |
| ingredients required package_size | PASS |  |
| ingredients required minimum_order_qty | PASS |  |
| ingredients required supplier_id | PASS |  |
| ingredients unique ingredient_name | PASS |  |
| ingredients FK supplier_id | PASS |  |
| products primary key | PASS |  |
| products required product_id | PASS |  |
| products required product_name | PASS |  |
| products required category_id | PASS |  |
| products required source_product_type_proxy | PASS |  |
| products required base_price_idr | PASS |  |
| products unique product_name | PASS |  |
| products FK category_id | PASS |  |
| recipes primary key | PASS |  |
| recipes required recipe_id | PASS |  |
| recipes required product_id | PASS |  |
| recipes required version | PASS |  |
| recipes unique product_id | PASS |  |
| recipes FK product_id | PASS |  |
| recipe_ingredients primary key | PASS |  |
| recipe_ingredients required recipe_ingredient_id | PASS |  |
| recipe_ingredients required recipe_id | PASS |  |
| recipe_ingredients required ingredient_id | PASS |  |
| recipe_ingredients required quantity | PASS |  |
| recipe_ingredients unique recipe_id,ingredient_id | PASS |  |
| recipe_ingredients FK recipe_id | PASS |  |
| recipe_ingredients FK ingredient_id | PASS |  |
| market_trends primary key | PASS |  |
| market_trends required trend_id | PASS |  |
| market_trends required region_id | PASS |  |
| market_trends required category_id | PASS |  |
| market_trends required week_start | PASS |  |
| market_trends required available_at | PASS |  |
| market_trends required interest_index | PASS |  |
| market_trends required provenance | PASS |  |
| market_trends unique category_id,week_start | PASS |  |
| market_trends FK category_id | PASS |  |
| market_trends FK region_id | PASS |  |
| market_trends timestamp available_at | PASS |  |
| social_posts primary key | PASS |  |
| social_posts required post_id | PASS |  |
| social_posts required platform | PASS |  |
| social_posts required source_post_key | PASS |  |
| social_posts required content_text | PASS |  |
| social_posts required published_at | PASS |  |
| social_posts required collected_at | PASS |  |
| social_posts required batch_key | PASS |  |
| social_posts required location_evidence | PASS |  |
| social_posts required language | PASS |  |
| social_posts required provenance | PASS |  |
| social_posts unique platform,source_post_key | PASS |  |
| social_posts FK region_id | PASS |  |
| social_posts timestamp published_at | PASS |  |
| social_posts period published_at | PASS |  |
| social_posts timestamp collected_at | PASS |  |
| menu_mentions primary key | PASS |  |
| menu_mentions required mention_id | PASS |  |
| menu_mentions required post_id | PASS |  |
| menu_mentions required product_id | PASS |  |
| menu_mentions required sentiment_label | PASS |  |
| menu_mentions required label_provenance | PASS |  |
| menu_mentions unique post_id,product_id | PASS |  |
| menu_mentions FK post_id | PASS |  |
| menu_mentions FK product_id | PASS |  |
| menu_aspects primary key | PASS |  |
| menu_aspects required menu_aspect_id | PASS |  |
| menu_aspects required mention_id | PASS |  |
| menu_aspects required aspect | PASS |  |
| menu_aspects required sentiment_label | PASS |  |
| menu_aspects unique mention_id,aspect | PASS |  |
| menu_aspects FK mention_id | PASS |  |
| menu_market_signals primary key | PASS |  |
| menu_market_signals required signal_id | PASS |  |
| menu_market_signals required region_id | PASS |  |
| menu_market_signals required product_id | PASS |  |
| menu_market_signals required period_start | PASS |  |
| menu_market_signals required available_at | PASS |  |
| menu_market_signals required source_max_published_at | PASS |  |
| menu_market_signals required post_count | PASS |  |
| menu_market_signals required positive_count | PASS |  |
| menu_market_signals required neutral_count | PASS |  |
| menu_market_signals required negative_count | PASS |  |
| menu_market_signals required mixed_count | PASS |  |
| menu_market_signals required sentiment_mean | PASS |  |
| menu_market_signals required provenance | PASS |  |
| menu_market_signals unique region_id,product_id,period_start | PASS |  |
| menu_market_signals FK region_id | PASS |  |
| menu_market_signals FK product_id | PASS |  |
| menu_market_signals timestamp available_at | PASS |  |
| menu_market_signals timestamp source_max_published_at | PASS |  |
| latent_demand primary key | PASS |  |
| latent_demand required demand_id | PASS |  |
| latent_demand required branch_id | PASS |  |
| latent_demand required product_id | PASS |  |
| latent_demand required transaction_at | PASS |  |
| latent_demand required requested_qty | PASS |  |
| latent_demand required unit_price_idr | PASS |  |
| latent_demand FK branch_id | PASS |  |
| latent_demand FK product_id | PASS |  |
| latent_demand timestamp transaction_at | PASS |  |
| latent_demand period transaction_at | PASS |  |
| transactions primary key | PASS |  |
| transactions required transaction_id | PASS |  |
| transactions required branch_id | PASS |  |
| transactions required transaction_at | PASS |  |
| transactions FK branch_id | PASS |  |
| transactions timestamp transaction_at | PASS |  |
| transactions period transaction_at | PASS |  |
| transaction_items primary key | PASS |  |
| transaction_items required transaction_item_id | PASS |  |
| transaction_items required transaction_id | PASS |  |
| transaction_items required demand_id | PASS |  |
| transaction_items required product_id | PASS |  |
| transaction_items required requested_qty | PASS |  |
| transaction_items required fulfilled_qty | PASS |  |
| transaction_items required unit_price_idr | PASS |  |
| transaction_items unique demand_id | PASS |  |
| transaction_items FK transaction_id | PASS |  |
| transaction_items FK demand_id | PASS |  |
| transaction_items FK product_id | PASS |  |
| purchase_orders primary key | PASS |  |
| purchase_orders required purchase_order_id | PASS |  |
| purchase_orders required branch_id | PASS |  |
| purchase_orders required supplier_id | PASS |  |
| purchase_orders required ordered_at | PASS |  |
| purchase_orders required expected_delivery_at | PASS |  |
| purchase_orders required status | PASS |  |
| purchase_orders FK branch_id | PASS |  |
| purchase_orders FK supplier_id | PASS |  |
| purchase_orders timestamp ordered_at | PASS |  |
| purchase_orders period ordered_at | PASS |  |
| purchase_orders timestamp expected_delivery_at | PASS |  |
| purchase_orders timestamp delivered_at | PASS |  |
| purchase_order_items primary key | PASS |  |
| purchase_order_items required purchase_order_item_id | PASS |  |
| purchase_order_items required purchase_order_id | PASS |  |
| purchase_order_items required ingredient_id | PASS |  |
| purchase_order_items required quantity | PASS |  |
| purchase_order_items required unit_cost_idr | PASS |  |
| purchase_order_items FK purchase_order_id | PASS |  |
| purchase_order_items FK ingredient_id | PASS |  |
| inventory_movements primary key | PASS |  |
| inventory_movements required movement_id | PASS |  |
| inventory_movements required branch_id | PASS |  |
| inventory_movements required ingredient_id | PASS |  |
| inventory_movements required movement_at | PASS |  |
| inventory_movements required movement_type | PASS |  |
| inventory_movements required quantity | PASS |  |
| inventory_movements FK branch_id | PASS |  |
| inventory_movements FK ingredient_id | PASS |  |
| inventory_movements FK transaction_item_id | PASS |  |
| inventory_movements FK purchase_order_item_id | PASS |  |
| inventory_movements timestamp movement_at | PASS |  |
| inventory_movements period movement_at | PASS |  |
| inventory_snapshots primary key | PASS |  |
| inventory_snapshots required snapshot_id | PASS |  |
| inventory_snapshots required branch_id | PASS |  |
| inventory_snapshots required ingredient_id | PASS |  |
| inventory_snapshots required date | PASS |  |
| inventory_snapshots required opening_stock | PASS |  |
| inventory_snapshots required receipts | PASS |  |
| inventory_snapshots required consumption | PASS |  |
| inventory_snapshots required waste | PASS |  |
| inventory_snapshots required adjustments | PASS |  |
| inventory_snapshots required closing_stock | PASS |  |
| inventory_snapshots unique branch_id,ingredient_id,date | PASS |  |
| inventory_snapshots FK branch_id | PASS |  |
| inventory_snapshots FK ingredient_id | PASS |  |
| stockout_events primary key | PASS |  |
| stockout_events required stockout_event_id | PASS |  |
| stockout_events required transaction_item_id | PASS |  |
| stockout_events required ingredient_id | PASS |  |
| stockout_events required event_at | PASS |  |
| stockout_events required shortage_qty | PASS |  |
| stockout_events required unfulfilled_product_qty | PASS |  |
| stockout_events FK transaction_item_id | PASS |  |
| stockout_events FK ingredient_id | PASS |  |
| stockout_events timestamp event_at | PASS |  |
| stockout_events period event_at | PASS |  |
| waste_records primary key | PASS |  |
| waste_records required waste_id | PASS |  |
| waste_records required movement_id | PASS |  |
| waste_records required reason | PASS |  |
| waste_records required quantity | PASS |  |
| waste_records FK movement_id | PASS |  |
| restock_decision_dataset primary key | PASS |  |
| restock_decision_dataset required decision_id | PASS |  |
| restock_decision_dataset required branch_id | PASS |  |
| restock_decision_dataset required ingredient_id | PASS |  |
| restock_decision_dataset required decision_at | PASS |  |
| restock_decision_dataset required history_days | PASS |  |
| restock_decision_dataset required mean_daily_consumption_14d | PASS |  |
| restock_decision_dataset required on_hand | PASS |  |
| restock_decision_dataset required on_order | PASS |  |
| restock_decision_dataset required lead_time_days | PASS |  |
| restock_decision_dataset required shelf_life_days | PASS |  |
| restock_decision_dataset required package_size | PASS |  |
| restock_decision_dataset required minimum_order_qty | PASS |  |
| restock_decision_dataset required baseline_purchase_qty | PASS |  |
| restock_decision_dataset required market_interest_latest | PASS |  |
| restock_decision_dataset required market_interest_lag_1w | PASS |  |
| restock_decision_dataset required market_feature_max_at | PASS |  |
| restock_decision_dataset required social_post_count_latest_month | PASS |  |
| restock_decision_dataset required menu_sentiment_latest_month | PASS |  |
| restock_decision_dataset required social_data_available | PASS |  |
| restock_decision_dataset required social_age_days | PASS |  |
| restock_decision_dataset required label_window_end | PASS |  |
| restock_decision_dataset required label_observed | PASS |  |
| restock_decision_dataset required split | PASS |  |
| restock_decision_dataset unique branch_id,ingredient_id,decision_at | PASS |  |
| restock_decision_dataset FK branch_id | PASS |  |
| restock_decision_dataset FK ingredient_id | PASS |  |
| restock_decision_dataset timestamp decision_at | PASS |  |
| restock_decision_dataset period decision_at | PASS |  |
| restock_decision_dataset timestamp market_feature_max_at | PASS |  |
| restock_decision_dataset timestamp social_feature_max_at | PASS |  |
| restock_decision_dataset timestamp social_available_at | PASS |  |
| restock_decision_dataset timestamp label_window_end | PASS |  |
| inventory_risk_ml_dataset primary key | PASS |  |
| inventory_risk_ml_dataset required risk_row_id | PASS |  |
| inventory_risk_ml_dataset required branch_id | PASS |  |
| inventory_risk_ml_dataset required ingredient_id | PASS |  |
| inventory_risk_ml_dataset required decision_at | PASS |  |
| inventory_risk_ml_dataset required history_days | PASS |  |
| inventory_risk_ml_dataset required mean_daily_consumption_14d | PASS |  |
| inventory_risk_ml_dataset required on_hand | PASS |  |
| inventory_risk_ml_dataset required on_order | PASS |  |
| inventory_risk_ml_dataset required lead_time_days | PASS |  |
| inventory_risk_ml_dataset required shelf_life_days | PASS |  |
| inventory_risk_ml_dataset required package_size | PASS |  |
| inventory_risk_ml_dataset required minimum_order_qty | PASS |  |
| inventory_risk_ml_dataset required baseline_purchase_qty | PASS |  |
| inventory_risk_ml_dataset required market_interest_latest | PASS |  |
| inventory_risk_ml_dataset required market_interest_lag_1w | PASS |  |
| inventory_risk_ml_dataset required market_feature_max_at | PASS |  |
| inventory_risk_ml_dataset required social_post_count_latest_month | PASS |  |
| inventory_risk_ml_dataset required menu_sentiment_latest_month | PASS |  |
| inventory_risk_ml_dataset required social_data_available | PASS |  |
| inventory_risk_ml_dataset required social_age_days | PASS |  |
| inventory_risk_ml_dataset required label_window_end | PASS |  |
| inventory_risk_ml_dataset required label_observed | PASS |  |
| inventory_risk_ml_dataset required split | PASS |  |
| inventory_risk_ml_dataset FK branch_id | PASS |  |
| inventory_risk_ml_dataset FK ingredient_id | PASS |  |
| inventory_risk_ml_dataset timestamp decision_at | PASS |  |
| inventory_risk_ml_dataset period decision_at | PASS |  |
| inventory_risk_ml_dataset timestamp market_feature_max_at | PASS |  |
| inventory_risk_ml_dataset timestamp social_feature_max_at | PASS |  |
| inventory_risk_ml_dataset timestamp social_available_at | PASS |  |
| inventory_risk_ml_dataset timestamp label_window_end | PASS |  |
| sentiment_ml_dataset primary key | PASS |  |
| sentiment_ml_dataset required sentiment_row_id | PASS |  |
| sentiment_ml_dataset required mention_id | PASS |  |
| sentiment_ml_dataset required post_id | PASS |  |
| sentiment_ml_dataset required product_id | PASS |  |
| sentiment_ml_dataset required published_at | PASS |  |
| sentiment_ml_dataset required collected_at | PASS |  |
| sentiment_ml_dataset required content_text | PASS |  |
| sentiment_ml_dataset required sentiment_label | PASS |  |
| sentiment_ml_dataset required label_provenance | PASS |  |
| sentiment_ml_dataset required split | PASS |  |
| sentiment_ml_dataset required text_fingerprint | PASS |  |
| sentiment_ml_dataset required training_status | PASS |  |
| sentiment_ml_dataset FK mention_id | PASS |  |
| sentiment_ml_dataset FK post_id | PASS |  |
| sentiment_ml_dataset FK product_id | PASS |  |
| sentiment_ml_dataset FK region_id | PASS |  |
| sentiment_ml_dataset timestamp published_at | PASS |  |
| sentiment_ml_dataset period published_at | PASS |  |
| sentiment_ml_dataset timestamp collected_at | PASS |  |
| trend_ml_dataset primary key | PASS |  |
| trend_ml_dataset required trend_row_id | PASS |  |
| trend_ml_dataset required category_id | PASS |  |
| trend_ml_dataset required decision_at | PASS |  |
| trend_ml_dataset required interest_lag_1w | PASS |  |
| trend_ml_dataset required label_observed | PASS |  |
| trend_ml_dataset required split | PASS |  |
| trend_ml_dataset FK category_id | PASS |  |
| trend_ml_dataset timestamp decision_at | PASS |  |
| trend_ml_dataset period decision_at | PASS |  |
| trend_ml_dataset timestamp feature_max_at | PASS |  |
| Nonnegative daily inventory | PASS |  |
| Daily conservation | PASS | max residual=3.5527137e-15 |
| Consecutive daily continuity | PASS |  |
| No negative stock at any movement | PASS | min=-3.552713678800501e-15 |
| Independent FEFO expiry and lot reconstruction | PASS | [] |
| Snapshot closing equals cumulative ledger | PASS |  |
| Ledger daily receipts | PASS |  |
| Ledger daily consumption | PASS |  |
| Ledger daily waste | PASS |  |
| Ledger daily adjustments | PASS |  |
| Every product has one recipe | PASS |  |
| Recipe positive valid units | PASS |  |
| Fulfilled quantity bounded | PASS |  |
| All recipe consumption reconciles per transaction item | PASS |  |
| Consumption movement branch matches transaction | PASS |  |
| Latent demand and transaction item identities | PASS |  |
| Supplier civil-date lead times | PASS |  |
| Delivery timestamps match planned schedule | PASS |  |
| Order supplier matches ingredient supplier | PASS |  |
| MOQ and package constraints | PASS |  |
| Receipts equal delivered purchase quantities | PASS |  |
| Receipt branch and ingredient match purchase order | PASS |  |
| Waste records reconcile ledger | PASS |  |
| All branches are Semarang WIB | PASS |  |
| No cafe-review tables or source files | PASS |  |
| Social posts are explicitly synthetic Instagram | PASS |  |
| No fabricated real Instagram URL or account | PASS |  |
| No purchase, cafe, or rating link in public discussion | PASS |  |
| Indonesian menu discussion provenance | PASS |  |
| Location uncertainty explicitly represented | PASS |  |
| Collection follows publication | PASS |  |
| Monthly Instagram collection schedule | PASS |  |
| Menu names occur in corresponding caption | PASS |  |
| Menu sentiment ground truth consistent with aspects | PASS |  |
| All four menu sentiment classes available | PASS |  |
| Monthly region/menu signals independently reconstructed | PASS | [] |
| Regional signals exclude unknown locations | PASS |  |
| Sentiment training rows retain correct caption and label | PASS |  |
| Social splits use ingestion time, not publication time | PASS |  |
| Uncollected terminal batches excluded from training | PASS |  |
| Canonical text fingerprints independently verified | PASS |  |
| Earliest-ingestion text eligibility independently verified | PASS |  |
| No eligible duplicate text within or across ML partitions | PASS |  |
| Pending collection never eligible | PASS |  |
| No future feature market_feature_max_at | PASS |  |
| No future feature social_feature_max_at | PASS |  |
| No future feature social_available_at | PASS |  |
| Independent historical operational and regional-menu feature reconstruction | PASS | [] |
| Censored targets are NULL | PASS |  |
| Future stockout labels independently reconstructed | PASS | [] |
| Baseline quantities independently reconstructed | PASS | [] |
| Market features independently reconstructed from past only | PASS | [] |
| Risk target agrees with decision evaluation target | PASS |  |
| Risk and restock shared fields exactly synchronized | PASS |  |
| Risk input allowlist exists and excludes target metadata | PASS |  |
| Training windows purged across split boundaries | PASS |  |
| Trend bounds and provenance | PASS |  |
| Trend features and targets independently reconstructed | PASS | [] |
| Trend features precede decisions | PASS |  |
| Trend terminal targets censored | PASS |  |
| Semarang trend region | PASS |  |
| All decision features finite | PASS |  |
| Hourly source distribution plausibility | PASS | max absolute probability difference=0.00191 |
| Synthetic sentiment distribution follows explicit assumptions | PASS | max difference=0.00266; tolerance=0.08000 |

## Generated summary
```json
{
  "table_rows": {
    "regions": 4,
    "branches": 3,
    "categories": 4,
    "suppliers": 2,
    "ingredients": 10,
    "products": 10,
    "recipes": 10,
    "recipe_ingredients": 25,
    "market_trends": 252,
    "social_posts": 6612,
    "menu_mentions": 6612,
    "menu_aspects": 13224,
    "menu_market_signals": 508,
    "latent_demand": 98128,
    "transactions": 98128,
    "transaction_items": 98128,
    "purchase_orders": 4294,
    "purchase_order_items": 4294,
    "inventory_movements": 222122,
    "inventory_snapshots": 10950,
    "stockout_events": 7733,
    "waste_records": 383,
    "restock_decision_dataset": 10950,
    "inventory_risk_ml_dataset": 10950,
    "sentiment_ml_dataset": 6612,
    "trend_ml_dataset": 212
  },
  "requested_units": 140084,
  "fulfilled_units": 129494,
  "unfulfilled_units": 10590,
  "sentiment_counts": {
    "positive": 2993,
    "negative": 1332,
    "neutral": 1307,
    "mixed": 980
  },
  "unknown_location_posts": 321,
  "social_pending_rows": 49,
  "stockout_target_counts": {
    "1.0": "5543",
    "0.0": "5197",
    "nan": "210"
  }
}
```

## Distribution comparisons
```json
{
  "hourly_max_probability_difference": 0.0019070579947023797,
  "sentiment_assumptions": {
    "positive": 0.45,
    "neutral": 0.2,
    "negative": 0.2,
    "mixed": 0.15
  },
  "sentiment_generated": {
    "positive": 0.45266182698124624,
    "negative": 0.2014519056261343,
    "neutral": 0.19767090139140955,
    "mixed": 0.1482153660012099
  },
  "quantity_source": {
    "1": 0.5845046809195525,
    "2": 0.393264304300008,
    "3": 0.02198959199549344,
    "4": 0.00015424233482657797,
    "6": 2.0118565412162344e-05,
    "8": 6.706188470720782e-05
  },
  "quantity_synthetic": {
    "1": 0.5938773846404696,
    "2": 0.384701614218164,
    "3": 0.021400619598891245,
    "4": 2.038154247513452e-05
  },
  "source_price_usd_quantiles": {
    "0.0": 0.8,
    "0.1": 2.2,
    "0.5": 3.0,
    "0.9": 4.25,
    "1.0": 45.0
  },
  "synthetic_price_idr_quantiles": {
    "0.0": 16000.0,
    "0.1": 18000.0,
    "0.5": 20000.0,
    "0.9": 28000.0,
    "1.0": 34000.0
  },
  "source_category_probabilities": {
    "Bakery": 0.15287427237855092,
    "Branded": 0.005009522787628423,
    "Coffee": 0.39174870570562514,
    "Coffee beans": 0.011755948389173529,
    "Drinking Chocolate": 0.07690656938222591,
    "Flavours": 0.04553501971619411,
    "Loose Tea": 0.008114488049572145,
    "Packaged Chocolate": 0.0032659137852410203,
    "Tea": 0.30478955980578876
  },
  "synthetic_product_counts": {
    "6": 20061,
    "1": 19535,
    "8": 13225,
    "10": 11654,
    "9": 7936,
    "3": 6404,
    "2": 6309,
    "4": 6263,
    "5": 3407,
    "7": 3334
  }
}
```

The fictional menu is a subset/proxy of source categories, so exact product/category marginals are not expected. Seasonal and trend effects intentionally perturb demand. Instagram-like text is synthetic Indonesian menu discussion, not a cafe review or actual scrape. USD source prices and synthetic IDR prices are reported separately, never compared as the same currency. This report contains actual checks, not predictive accuracy or claims of business optimality.