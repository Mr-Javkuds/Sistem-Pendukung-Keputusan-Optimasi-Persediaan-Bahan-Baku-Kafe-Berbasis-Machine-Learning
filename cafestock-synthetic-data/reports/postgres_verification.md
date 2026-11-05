# PostgreSQL verification

PASS: schema parsed, all CSV tables imported in a fresh disposable cluster; all database row counts equal CSV row counts.

PostgreSQL 18.1 on x86_64-windows, compiled by msvc-19.44.35219, 64-bit

Six negative cases rejected: duplicate PK, orphan FK, negative package, overfulfilled item, inventory conservation violation, deletion of referenced ingredient. Each case was rolled back in a subtransaction. SQL import uses explicit columns, UTF-8 and NULL empty fields.

```json
{
  "branches": 3,
  "categories": 4,
  "ingredients": 10,
  "inventory_movements": 222122,
  "inventory_risk_ml_dataset": 10950,
  "inventory_snapshots": 10950,
  "latent_demand": 98128,
  "market_trends": 252,
  "menu_aspects": 13224,
  "menu_market_signals": 508,
  "menu_mentions": 6612,
  "products": 10,
  "purchase_orders": 4294,
  "purchase_order_items": 4294,
  "recipes": 10,
  "recipe_ingredients": 25,
  "regions": 4,
  "restock_decision_dataset": 10950,
  "sentiment_ml_dataset": 6612,
  "social_posts": 6612,
  "stockout_events": 7733,
  "suppliers": 2,
  "transactions": 98128,
  "transaction_items": 98128,
  "trend_ml_dataset": 212,
  "waste_records": 383
}
```
