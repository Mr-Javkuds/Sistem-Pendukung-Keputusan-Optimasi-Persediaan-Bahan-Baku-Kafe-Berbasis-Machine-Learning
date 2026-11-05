# PostgreSQL verification

PASS: schema parsed, all CSV tables imported in a fresh disposable cluster; all database row counts equal CSV row counts.

PostgreSQL 18.1 on x86_64-windows, compiled by msvc-19.44.35219, 64-bit

Six negative cases rejected: duplicate PK, orphan FK, negative package, overfulfilled item, inventory conservation violation, deletion of referenced ingredient. Each case was rolled back in a subtransaction. SQL import uses explicit columns, UTF-8 and NULL empty fields.

```json
{
  "branches": 3,
  "categories": 4,
  "customer_reviews": 3083,
  "ingredients": 10,
  "inventory_movements": 214836,
  "inventory_risk_ml_dataset": 10950,
  "inventory_snapshots": 10950,
  "latent_demand": 98492,
  "market_trends": 252,
  "products": 10,
  "purchase_orders": 4098,
  "purchase_order_items": 4098,
  "recipes": 10,
  "recipe_ingredients": 25,
  "restock_decision_dataset": 10950,
  "review_aspects": 5426,
  "sentiment_ml_dataset": 3083,
  "stockout_events": 8335,
  "suppliers": 2,
  "transactions": 98492,
  "transaction_items": 98492,
  "trend_ml_dataset": 212,
  "waste_records": 403
}
```
