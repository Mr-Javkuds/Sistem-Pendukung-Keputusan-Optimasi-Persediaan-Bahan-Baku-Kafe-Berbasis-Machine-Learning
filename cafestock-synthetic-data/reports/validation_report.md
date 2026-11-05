# Validation report

144/144 checks passed.

| Check | Result | Detail |
|---|---|---|
| branches primary key | PASS |  |
| branches unique branch_name | PASS |  |
| categories primary key | PASS |  |
| categories unique category_name | PASS |  |
| suppliers primary key | PASS |  |
| ingredients primary key | PASS |  |
| ingredients unique ingredient_name | PASS |  |
| ingredients FK supplier_id | PASS |  |
| products primary key | PASS |  |
| products unique product_name | PASS |  |
| products FK category_id | PASS |  |
| recipes primary key | PASS |  |
| recipes unique product_id | PASS |  |
| recipes FK product_id | PASS |  |
| recipe_ingredients primary key | PASS |  |
| recipe_ingredients unique recipe_id,ingredient_id | PASS |  |
| recipe_ingredients FK recipe_id | PASS |  |
| recipe_ingredients FK ingredient_id | PASS |  |
| market_trends primary key | PASS |  |
| market_trends unique category_id,week_start | PASS |  |
| market_trends FK category_id | PASS |  |
| market_trends timestamp available_at | PASS |  |
| latent_demand primary key | PASS |  |
| latent_demand FK branch_id | PASS |  |
| latent_demand FK product_id | PASS |  |
| latent_demand timestamp transaction_at | PASS |  |
| latent_demand period transaction_at | PASS |  |
| transactions primary key | PASS |  |
| transactions FK branch_id | PASS |  |
| transactions timestamp transaction_at | PASS |  |
| transactions period transaction_at | PASS |  |
| transaction_items primary key | PASS |  |
| transaction_items unique demand_id | PASS |  |
| transaction_items FK transaction_id | PASS |  |
| transaction_items FK demand_id | PASS |  |
| transaction_items FK product_id | PASS |  |
| customer_reviews primary key | PASS |  |
| customer_reviews FK transaction_item_id | PASS |  |
| customer_reviews timestamp review_at | PASS |  |
| customer_reviews period review_at | PASS |  |
| review_aspects primary key | PASS |  |
| review_aspects unique review_id,aspect | PASS |  |
| review_aspects FK review_id | PASS |  |
| purchase_orders primary key | PASS |  |
| purchase_orders FK branch_id | PASS |  |
| purchase_orders FK supplier_id | PASS |  |
| purchase_orders timestamp ordered_at | PASS |  |
| purchase_orders period ordered_at | PASS |  |
| purchase_orders timestamp expected_delivery_at | PASS |  |
| purchase_orders timestamp delivered_at | PASS |  |
| purchase_order_items primary key | PASS |  |
| purchase_order_items FK purchase_order_id | PASS |  |
| purchase_order_items FK ingredient_id | PASS |  |
| inventory_movements primary key | PASS |  |
| inventory_movements FK branch_id | PASS |  |
| inventory_movements FK ingredient_id | PASS |  |
| inventory_movements FK transaction_item_id | PASS |  |
| inventory_movements FK purchase_order_item_id | PASS |  |
| inventory_movements timestamp movement_at | PASS |  |
| inventory_movements period movement_at | PASS |  |
| inventory_snapshots primary key | PASS |  |
| inventory_snapshots unique branch_id,ingredient_id,date | PASS |  |
| inventory_snapshots FK branch_id | PASS |  |
| inventory_snapshots FK ingredient_id | PASS |  |
| stockout_events primary key | PASS |  |
| stockout_events FK transaction_item_id | PASS |  |
| stockout_events FK ingredient_id | PASS |  |
| stockout_events timestamp event_at | PASS |  |
| stockout_events period event_at | PASS |  |
| waste_records primary key | PASS |  |
| waste_records FK movement_id | PASS |  |
| restock_decision_dataset primary key | PASS |  |
| restock_decision_dataset unique branch_id,ingredient_id,decision_at | PASS |  |
| restock_decision_dataset FK branch_id | PASS |  |
| restock_decision_dataset FK ingredient_id | PASS |  |
| restock_decision_dataset timestamp decision_at | PASS |  |
| restock_decision_dataset period decision_at | PASS |  |
| restock_decision_dataset timestamp market_feature_max_at | PASS |  |
| restock_decision_dataset timestamp sentiment_feature_max_at | PASS |  |
| restock_decision_dataset timestamp label_window_end | PASS |  |
| inventory_risk_ml_dataset primary key | PASS |  |
| inventory_risk_ml_dataset FK branch_id | PASS |  |
| inventory_risk_ml_dataset FK ingredient_id | PASS |  |
| inventory_risk_ml_dataset timestamp decision_at | PASS |  |
| inventory_risk_ml_dataset period decision_at | PASS |  |
| inventory_risk_ml_dataset timestamp market_feature_max_at | PASS |  |
| inventory_risk_ml_dataset timestamp sentiment_feature_max_at | PASS |  |
| inventory_risk_ml_dataset timestamp label_window_end | PASS |  |
| sentiment_ml_dataset primary key | PASS |  |
| sentiment_ml_dataset FK review_id | PASS |  |
| sentiment_ml_dataset timestamp review_at | PASS |  |
| sentiment_ml_dataset period review_at | PASS |  |
| trend_ml_dataset primary key | PASS |  |
| trend_ml_dataset FK category_id | PASS |  |
| trend_ml_dataset timestamp decision_at | PASS |  |
| trend_ml_dataset period decision_at | PASS |  |
| trend_ml_dataset timestamp feature_max_at | PASS |  |
| Nonnegative daily inventory | PASS |  |
| Daily conservation | PASS | max residual=3.5527137e-15 |
| Consecutive daily continuity | PASS |  |
| No negative stock at any movement | PASS | min=-1.7763568394002505e-15 |
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
| Reviews reference fulfilled purchases | PASS |  |
| Reviews follow purchase | PASS |  |
| Sentiment follows documented rules | PASS |  |
| Mixed reviews contain opposed aspects | PASS |  |
| No unrelated cafe names | PASS |  |
| No copied source reviews | PASS |  |
| No future feature market_feature_max_at | PASS |  |
| No future feature sentiment_feature_max_at | PASS |  |
| Independent historical feature reconstruction | PASS | [] |
| Censored targets are NULL | PASS |  |
| Future stockout labels independently reconstructed | PASS | [] |
| Baseline quantities independently reconstructed | PASS | [] |
| Market features independently reconstructed from past only | PASS | [] |
| Risk target agrees with decision evaluation target | PASS |  |
| Training windows purged across split boundaries | PASS |  |
| Trend bounds and provenance | PASS |  |
| Trend features and targets independently reconstructed | PASS | [] |
| Trend features precede decisions | PASS |  |
| Trend terminal targets censored | PASS |  |
| Synthetic review provenance | PASS |  |
| Review rating bounds | PASS |  |
| All decision features finite | PASS |  |
| Hourly source distribution plausibility | PASS | max absolute probability difference=0.00308 |
| Rating source distribution plausibility | PASS | max difference=0.00663; tolerance=0.08000 |

## Generated summary
```json
{
  "table_rows": {
    "branches": 3,
    "categories": 4,
    "suppliers": 2,
    "ingredients": 10,
    "products": 10,
    "recipes": 10,
    "recipe_ingredients": 25,
    "market_trends": 252,
    "latent_demand": 98492,
    "transactions": 98492,
    "transaction_items": 98492,
    "customer_reviews": 3083,
    "review_aspects": 5426,
    "purchase_orders": 4098,
    "purchase_order_items": 4098,
    "inventory_movements": 214836,
    "inventory_snapshots": 10950,
    "stockout_events": 8335,
    "waste_records": 403,
    "restock_decision_dataset": 10950,
    "inventory_risk_ml_dataset": 10950,
    "sentiment_ml_dataset": 3083,
    "trend_ml_dataset": 212
  },
  "requested_units": 140263,
  "fulfilled_units": 129096,
  "unfulfilled_units": 11167,
  "sentiment_counts": {
    "positive": 1981,
    "mixed": 622,
    "negative": 251,
    "neutral": 229
  },
  "stockout_target_counts": {
    "1.0": "5890",
    "0.0": "4850",
    "nan": "210"
  }
}
```

## Distribution comparisons
```json
{
  "hourly_max_probability_difference": 0.0030786974733137684,
  "rating_source": {
    "1": 0.036587129428778016,
    "2": 0.058279103398409256,
    "3": 0.09689081706435286,
    "4": 0.3099060014461316,
    "5": 0.49833694866232825
  },
  "rating_synthetic": {
    "5": 0.5027570548167369,
    "4": 0.3032760298410639,
    "3": 0.09276678559844308,
    "2": 0.06162828413882582,
    "1": 0.03957184560493026
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
    "1": 0.5977338260975511,
    "2": 0.38042683669739674,
    "3": 0.021839337205052187
  },
  "source_price_quantiles": {
    "0.0": 0.8,
    "0.1": 2.2,
    "0.5": 3.0,
    "0.9": 4.25,
    "1.0": 45.0
  },
  "synthetic_price_quantiles": {
    "0.0": 2.0,
    "0.1": 2.5,
    "0.5": 3.25,
    "0.9": 4.25,
    "1.0": 9.25
  },
  "source_review_length_quantiles": {
    "0.0": 5.0,
    "0.1": 27.0,
    "0.5": 81.0,
    "0.9": 207.0,
    "1.0": 945.0
  },
  "synthetic_review_length_quantiles": {
    "0.0": 21.0,
    "0.1": 39.0,
    "0.5": 88.0,
    "0.9": 180.0,
    "1.0": 193.0
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
    "6": 20167,
    "1": 19443,
    "8": 13102,
    "10": 11975,
    "9": 7927,
    "7": 6684,
    "3": 6420,
    "4": 6329,
    "2": 6266,
    "5": 179
  }
}
```

The fictional menu is a subset/proxy of source categories, so exact product/category marginals are not expected. Seasonal and trend effects intentionally perturb demand. Review lengths are capped at 180 target words plus one filler sentence; this differs from long Yelp outliers. Source sentiment codes have no verified semantics and are not treated as labels. This report contains actual checks, not predictive accuracy or claims of business optimality.