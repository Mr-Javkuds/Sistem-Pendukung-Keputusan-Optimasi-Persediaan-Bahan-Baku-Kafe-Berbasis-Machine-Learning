# Referensi awal — CafeStock Synthetic Dataset Generator

> **Dokumen historis, bukan spesifikasi aktif.** Ketentuan NYC/Yelp dan ulasan
> kafe di bawah telah digantikan oleh skenario Semarang dan Instagram sintetis.
> Mulai dari [README proyek](README.md) dan ikuti
> [alur serta progres terkini](cafestock-synthetic-data/docs/alur_project_ml.md).
> Teks asli dipertahankan untuk menelusuri rancangan awal.

## 1. ROLE & OBJECTIVE

You are a Senior Data Engineer specializing in synthetic data generation, relational database design, statistical modeling, and reproducible research.

Build a complete Python-based synthetic dataset generator for an academic project named **CafeStock Intelligence**.

The objective is to create a unified, statistically plausible, relationally consistent historical dataset for a fictional multi-branch cafe business.

The dataset will later be used for:

- Machine learning-based market trend analysis.
- Customer sentiment analysis.
- Ingredient inventory risk classification.
- Ingredient restock quantity recommendations.
- Inventory optimization backtesting.
- PostgreSQL database implementation.

**Your responsibility is DATA GENERATION ONLY.**

Do not build a frontend, backend API, dashboard, or production machine learning model.

Do not train the final prediction models. Only prepare the datasets, labels, validation scripts, and database schema required for subsequent experiments.

---

## 2. INPUT FILES

Locate and inspect these six source files in the current workspace:

1. `coffee-shop-sales-revenue.csv`
2. `geoMap.csv`
3. `geoMap(1).csv`
4. `raw_yelp_review_data.csv`
5. `ratings_and_sentiments.csv`
6. `sentiments_by_shop.csv`

Do not assume their schemas.

Use Python to inspect actual file structures.

Detect:

- Delimiters and encodings.
- Column names and data types.
- Row counts.
- Missing values and duplicates.
- Date ranges.
- Transaction distributions.
- Product categories and prices.
- Review ratings and sentiment distributions.
- Google Trends data format.

The transaction CSV may use a pipe delimiter.

Determine whether the Google Trends files contain geographic data or time-series data.

If files are missing, report them explicitly. Do not fabricate source observations.

Save the results to:

`reports/source_audit.md`

---

## 3. UNIFIED BUSINESS CONTEXT

Create one fictional cafe company:

**Business:** CafeStock Coffee

**Region:** New York City, USA

**Branches:**

- Lower Manhattan
- Hell's Kitchen
- Astoria

**Historical simulation period:**

2025-11-04 through 2026-11-03.

Use one shared catalog of products and ingredients.

All transactions, customer reviews, inventory records, purchase orders, supplier records, and market trends must belong to this coherent business scenario.

Use stable primary keys and foreign keys.

The source files originate from different businesses and periods. Therefore, do not directly merge them using arbitrary IDs or assume they describe the same customers, products, or branches.

---

## 4. GENERATION STRATEGY

Use a source-informed synthetic generation approach.

### Historical transactions

Learn statistical properties from the transaction dataset:

- Hourly transaction patterns.
- Day-of-week distributions.
- Product popularity.
- Product quantity distributions.
- Price distributions.
- Branch-level differences.
- Category-level purchasing behavior.

Generate new synthetic transactions using conditional sampling, bootstrapping, or appropriate probabilistic distributions.

Introduce realistic seasonal and random variation.

Do not copy entire source transactions.

### Google Trends

Inspect both Google Trends files.

If they contain only geographic interest, do not treat them as measured historical time-series data.

Generate a synthetic weekly market-interest series with:

- Seasonal variation.
- Autocorrelation.
- Random fluctuations.
- Category-specific differences.
- Plausible delayed associations with menu demand.

Use a normalized index from 0 to 100.

Preserve original Google Trends observations separately.

Document all simulated trend assumptions.

### Customer reviews

Learn rating, sentiment, review-length, and aspect distributions from the Yelp datasets.

Generate original synthetic reviews referencing CafeStock Coffee products and branches.

Include:

- Positive reviews.
- Neutral reviews.
- Negative reviews.
- Mixed-sentiment reviews.
- Product-specific opinions.
- Service-related opinions.

Do not copy real review texts or use unrelated cafe names.

Keep review dates consistent with the simulation period.

Create sentiment ground-truth labels based on documented generation rules.

Do not use labels predicted by the future sentiment model as ground truth.

---

## 5. PRODUCT RECIPES & INGREDIENTS

Create a standardized recipe catalog.

Every product included in inventory analysis must have a recipe.

Example:

Iced Matcha Latte:

- Matcha powder: 5 g.
- Milk: 200 ml.
- Ice: 150 g.
- Sweetener: 15 ml.

Create:

- Product catalog.
- Ingredient catalog.
- Recipe ingredient mappings.
- Ingredient quantities.
- Units of measurement.
- Shelf-life attributes.
- Ingredient purchase costs.

Use plausible recipe assumptions and document them.

Do not claim that recipe quantities originate from the Kaggle transaction dataset.

All unit conversions must be valid.

---

## 6. HISTORICAL INVENTORY SIMULATION

Generate inventory data derived from transactions and recipes.

Include:

- Opening stock.
- Ingredient consumption.
- Supplier purchases.
- Supplier deliveries.
- Inventory adjustments.
- Ingredient waste.
- Stockout events.
- Closing stock.
- Supplier lead times.
- Supplier minimum order quantities.
- Purchase package sizes.

Inventory must obey conservation rules:

Closing Stock =
Opening Stock + Receipts - Consumption - Waste + Adjustments.

Implement the simulation chronologically.

Transactions must consume the ingredients required by their recipes.

Do not allow inventory to become negative.

If ingredients are unavailable, record unfulfilled demand or reduce fulfilled transactions accordingly.

Distinguish observed sales from simulated latent demand.

Use a historical baseline restocking policy to generate purchase orders.

Avoid constructing inventory outcomes directly from the future ML recommendation labels.

---

## 7. RESTOCK DECISION DATASET

Generate historical restock decision snapshots.

Each snapshot must represent information available at a specific decision timestamp.

Include:

- Branch ID.
- Ingredient ID.
- Decision timestamp.
- Historical ingredient consumption.
- Inventory on hand.
- Inventory already on order.
- Supplier lead time.
- Shelf life.
- Package size.
- Minimum order quantity.
- Historical market trend features.
- Historical sentiment features.
- Future stockout outcome for evaluation.
- Baseline recommended purchase quantity.

Generate a reference restock quantity using a documented baseline policy or constrained optimization method.

Do not label arbitrary purchase quantities as mathematically optimal.

If an oracle quantity is generated using future information, store it separately as an evaluation target and never expose future information in input features.

The application will eventually display recommended ingredient purchase quantities, not product-level sales forecasts.

---

## 8. OUTPUT DATASETS

Save generated datasets as UTF-8 CSV files inside `output/`.

### Business entities

- `branches.csv`
- `products.csv`
- `categories.csv`
- `ingredients.csv`
- `recipes.csv`
- `recipe_ingredients.csv`
- `suppliers.csv`

### Historical transactions

- `transactions.csv`
- `transaction_items.csv`

### Market and customer data

- `market_trends.csv`
- `customer_reviews.csv`
- `review_aspects.csv`

### Inventory and purchasing

- `inventory_movements.csv`
- `inventory_snapshots.csv`
- `purchase_orders.csv`
- `purchase_order_items.csv`
- `stockout_events.csv`
- `waste_records.csv`

### Machine learning preparation

- `trend_ml_dataset.csv`
- `sentiment_ml_dataset.csv`
- `inventory_risk_ml_dataset.csv`
- `restock_decision_dataset.csv`

Every table must contain consistent IDs, documented fields, and valid relationships.

---

## 9. DATA QUALITY VALIDATION

Implement automated validation scripts.

Check:

1. Primary key uniqueness.
2. Foreign key integrity.
3. No orphan records.
4. Valid timestamps.
5. No unexplained negative inventory.
6. Inventory conservation.
7. Recipe quantity consistency.
8. Supplier lead-time consistency.
9. Transaction and ingredient consumption consistency.
10. Review-to-product and review-to-branch consistency.
11. Realistic statistical distributions.
12. No future-data leakage.
13. Reproducibility using a fixed random seed.
14. Correct distinction between source-derived and simulated data.

Generate:

`reports/validation_report.md`

Include summary statistics, distribution comparisons, and validation failures.

Do not silently repair invalid records without documenting the correction.

---

## 10. DATABASE DESIGN

Create a PostgreSQL-compatible relational schema.

Requirements:

- Primary keys.
- Foreign keys.
- Appropriate constraints.
- Relevant indexes.
- Consistent data types.
- Normalization to at least 3NF where practical.

Generate:

- `sql/schema.sql`
- `sql/import.sql`
- `docs/data_dictionary.md`
- `docs/erd.md`

The ERD must describe the relationships between products, transactions, recipes, ingredients, inventory, suppliers, market trends, and customer reviews.

Ensure generated CSV files can be imported using the provided SQL scripts.

---

## 11. PROJECT STRUCTURE

Organize the project as:

```text
cafestock-synthetic-data/
├── input/
│   ├── coffee-shop-sales-revenue.csv
│   ├── geoMap.csv
│   ├── geoMap(1).csv
│   ├── raw_yelp_review_data.csv
│   ├── ratings_and_sentiments.csv
│   └── sentiments_by_shop.csv
├── src/
│   ├── audit.py
│   ├── profile.py
│   ├── generate_transactions.py
│   ├── generate_trends.py
│   ├── generate_reviews.py
│   ├── generate_recipes.py
│   ├── simulate_inventory.py
│   ├── generate_ml_datasets.py
│   └── validate.py
├── output/
├── reports/
├── docs/
├── sql/
│   ├── schema.sql
│   └── import.sql
├── config.yaml
├── requirements.txt
├── generate.py
└── README.md
```

Use Python 3.11+.

Prefer pandas, numpy, scipy, and standard Python libraries.

Use a fixed random seed.

Make dataset size and simulation dates configurable.

Do not require paid APIs or cloud services.

---

## 12. EXECUTION WORKFLOW

Execute the task in this order.

**Step 1 — Audit**

Inspect all six input files and generate a source audit.

**Step 2 — Statistical profiling**

Extract source distributions and identify data limitations.

**Step 3 — Schema design**

Define the unified business entities and relational structure.

**Step 4 — Synthetic generation**

Generate transactions, market trends, and customer reviews.

**Step 5 — Operational modeling**

Create recipes, suppliers, historical purchasing, and inventory movements.

**Step 6 — ML dataset preparation**

Create training-ready feature tables and evaluation labels.

**Step 7 — Validation**

Run automated integrity and statistical checks.

**Step 8 — Export**

Export CSV files, PostgreSQL schema, data dictionary, and documentation.

**Step 9 — Final verification**

Run the generator from a clean configuration and confirm reproducibility.

---

## 13. ACCEPTANCE CRITERIA

The task is complete only when:

- All six input files have been audited.
- All synthetic records belong to the same fictional cafe business.
- The generated datasets share valid relational keys.
- Inventory quantities reconcile with historical movements.
- Restock decision snapshots contain no future information.
- Dataset generation is deterministic for a fixed seed.
- All required CSV files are generated.
- PostgreSQL import scripts are provided.
- Validation tests pass.
- Every synthetic assumption is documented.

If a validation test fails, fix the underlying generator rather than weakening the validation.

Do not fabricate success metrics.

## FINAL INSTRUCTION

Implement the complete synthetic data generation pipeline, not just a conceptual proposal.

Begin by inspecting the actual CSV files in the workspace.

Before generating data, report the source schemas, data quality issues, and modeling assumptions.

Then implement, execute, test, and document the generator.

The final deliverable must be a reproducible, research-oriented synthetic dataset generator suitable for subsequent machine learning and database experiments.
