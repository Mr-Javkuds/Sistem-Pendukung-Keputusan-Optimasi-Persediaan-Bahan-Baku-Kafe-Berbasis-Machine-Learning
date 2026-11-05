# Entity relationships

```mermaid
erDiagram
    regions ||--o{ branches : region_id
    suppliers ||--o{ ingredients : supplier_id
    categories ||--o{ products : category_id
    products ||--o| recipes : product_id
    recipes ||--o{ recipe_ingredients : recipe_id
    ingredients ||--o{ recipe_ingredients : ingredient_id
    categories ||--o{ market_trends : category_id
    regions ||--o{ market_trends : region_id
    regions o|--o{ social_posts : region_id
    social_posts ||--o{ menu_mentions : post_id
    products ||--o{ menu_mentions : product_id
    menu_mentions ||--o{ menu_aspects : mention_id
    regions ||--o{ menu_market_signals : region_id
    products ||--o{ menu_market_signals : product_id
    branches ||--o{ latent_demand : branch_id
    products ||--o{ latent_demand : product_id
    branches ||--o{ transactions : branch_id
    transactions ||--o{ transaction_items : transaction_id
    latent_demand ||--o{ transaction_items : demand_id
    products ||--o{ transaction_items : product_id
    branches ||--o{ purchase_orders : branch_id
    suppliers ||--o{ purchase_orders : supplier_id
    purchase_orders ||--o{ purchase_order_items : purchase_order_id
    ingredients ||--o{ purchase_order_items : ingredient_id
    branches ||--o{ inventory_movements : branch_id
    ingredients ||--o{ inventory_movements : ingredient_id
    transaction_items o|--o{ inventory_movements : transaction_item_id
    purchase_order_items o|--o{ inventory_movements : purchase_order_item_id
    branches ||--o{ inventory_snapshots : branch_id
    ingredients ||--o{ inventory_snapshots : ingredient_id
    transaction_items ||--o{ stockout_events : transaction_item_id
    ingredients ||--o{ stockout_events : ingredient_id
    inventory_movements ||--o{ waste_records : movement_id
    branches ||--o{ restock_decision_dataset : branch_id
    ingredients ||--o{ restock_decision_dataset : ingredient_id
    branches ||--o{ inventory_risk_ml_dataset : branch_id
    ingredients ||--o{ inventory_risk_ml_dataset : ingredient_id
    menu_mentions ||--o{ sentiment_ml_dataset : mention_id
    social_posts ||--o{ sentiment_ml_dataset : post_id
    products ||--o{ sentiment_ml_dataset : product_id
    regions o|--o{ sentiment_ml_dataset : region_id
    categories ||--o{ trend_ml_dataset : category_id
```

Every FK child has exactly one parent (1..1), except optional movement references and unknown social locations (0..1). Every parent permits 0..N children; recipes.product_id is UNIQUE, so a product permits 0..1 recipe in SQL and exactly one in this generated catalog, enforced by validation. Products and ingredients have a binary N:M relation through recipe_ingredients. Social posts have no purchase/transaction FK. Menu mentions connect external discussion to products; regions connect the market to branches. Unknown locations do not contribute to regional aggregates. No actual Instagram account, customer identity or real post URL is fabricated.

Operational entities are normalized to 3NF. ML tables deliberately duplicate decision-time supplier attributes and social text as immutable experiment snapshots. Recipe, conservation, FEFO, cross-table supplier consistency and temporal rules are enforced by the Python validator; they are not guaranteed by row CHECK constraints alone.

Indexes support FK joins, branch/time sales filters, ingredient movement reconstruction and social-data availability windows. Performance has not been benchmarked. No production migration is run. Rollback: discard the disposable database; this deletes its data and does not restore previous data.