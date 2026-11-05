# Generation assumptions and provenance

CafeStock Coffee is fictional. Three NYC branches run from 2025-11-04 through
2026-11-03 inclusive. No source business/customer IDs are joined to this company.
Every row in output/ is simulated. Source bytes in input/ are preserved unchanged
and hashed. All reported source counts precede profiling exclusions.

## Source use

The pipe-delimited transaction CSV informs branch exposure, hourly patterns,
weekday rates per observed calendar day, product-type popularity, conditional
quantity and price samples. The source locations happen to match the requested
fictional branch names: mapping uses names, never source store IDs. Sampling
retains conditional quantity/price pairs within a product-type pool, generates
new dates/times and assigns new IDs; no whole original transaction is copied.
The source period is January–June 2023. No claim of measured 2025–26 demand is made.
The default scale is 90 attempted transactions per branch per day, before seasonal
effects, weekday effects and source branch weights; one line per transaction.

The 10-product fictional menu uses source product-type proxies. Several source
types (retail beans, branded goods, loose tea) are intentionally excluded from
inventory analysis. Iced Matcha Latte uses a green-tea category fallback if its
proxy has no exact source type. Blueberry Muffin uses the source Scone proxy.
Prices are synthetic transaction-level USD prices sampled within the proxy;
no single immutable list price is assumed. Quantities count product portions.

Raw Yelp reviews are deduplicated for rating and length statistics (701 exact
duplicates excluded). The audit still reports all original rows. Transformed
sentiment data excludes rows missing text/rating, drops exact duplicates, and
coerces aspect values numerically. Invalid/missing aspect values count as absent
for the *mention proxy only*; inputs are never rewritten. Integer sentiment
scales have no supplied codebook and are never used as ground truth. The shop
aggregates are audited as overlapping evidence, not pooled as independent reviews.
The rating distribution is empirical; source review lengths parameterize a
lognormal target with median equal to the empirical median, sigma 0.65, capped
at 20–180 words plus one sentence. Reviews are original template compositions,
not paraphrases of real reviews. They have lower linguistic diversity than real
Yelp text: models evaluated on them measure recovery of these rules, not real-world
sentiment performance. Some neutral filler repeats. Dates embedded in raw review
text are not verified publication timestamps and are not remapped into CafeStock.

geoMap.csv contains geographic interest with missing city values; these stay
missing. geoMap(1).csv is absent. multiTimeline.csv contains actual weekly matcha
interest in Central Java (53 points); it is an additional preserved source, not
a replacement geographic export and not measured NYC history. Neither Google
file calibrates NYC demand. The supplied parquet is an unused alternative sales
container; the CSV is authoritative for this pipeline. Source observations are
preserved in input/, separate from all generated output.

## Market and review rules

Weekly category interest uses 52 + 16*sin(2*pi*(dayofyear/365.25+category_id/8))
plus AR(1) noise with coefficient 0.72 and innovation SD 4, clipped to [0,100].
Ten synthetic pre-period weeks warm up lag features. Index availability is midnight
at the start of the synthetic week, explicitly invented rather than claimed as
Google publication timing. Demand weights multiply exp(0.012*(index-50)) using
only an index at least seven days old. Daily seasonal amplitude is 10%; branch/day
transaction counts are Poisson. All these constants are assumptions.

Reviews are sampled only from fulfilled purchases, with configured probability.
Ratings >=4 imply positive; <=2 negative; 3 neutral. Independently, 20% become
mixed: product and service have opposing polarities. Product prose follows its
aspect label; service prose follows its own. Optional vibe, price and seating
mentions follow numerically parsed source mention proxies and the product polarity.
The product always appears; mixed reviews always mention service. Ground truth
comes from these explicit composition rules, never an inferred model label.
Publication is 15–119 minutes after purchase, within the simulation business day.
Reviews contain product and branch names inherited from their purchased item;
they do not carry redundant branch/product FKs. There is no synthetic customer ID.

## Recipes and inventory

Recipes, supplier names, costs, package sizes and shelf lives are engineering
assumptions in src/generate_recipes.py, not Kaggle measurements. Coffee 18 g per
portion; latte milk 180–200 ml; matcha 5 g + 200 ml milk + 150 g ice + 15 ml syrup;
tea 3–4 g; chocolate 25 g + 220 ml milk; bakery goods consume one prepared portion.
Water is tracked as bought filtered-water containers; ice is purchased in bags.
No conversion between g and ml is made; base units are g, ml or piece. A recipe
quantity always uses its ingredient's unit; price is USD per base unit.

Inventory uses FEFO lots. Initial stock covers two prior-estimated demand days,
rounded to package sizes. Initial usage prior is the equal-menu recipe average
times configured daily transaction count times 1.5 portions, never future sales.
Initial lots expire after the ingredient shelf life. At 01:00 expired lots are
waste, at 02:00 an independent 0.8% daily chance records physical shrinkage of up
to 2% of a package, at 04:00 scheduled deliveries arrive, at 05:00 decisions are
made. Source-informed service hours are 06:00–20:59. Consumption is immediate.
No negative lots or fractional fulfilled product portions are allowed. Full
requested demand is saved; unfulfilled portions do not consume any ingredients.
Stockout events identify ingredients that physically constrain an attempted sale;
the same unfulfilled product may have multiple ingredient causes. Do not sum
unfulfilled_product_qty across stockout causes to estimate lost product units.
Use transaction_items requested_qty minus fulfilled_qty instead. transactions
records all attempts, including zero-fulfilled attempts, to preserve this distinction.

Suppliers have deterministic civil-calendar lead times of 1 or 3 days, including
weekends. Receipt at 04:00 after a 05:00 order means elapsed hours are lead*24-1,
with DST adjustment; compare NYC calendar dates, not a fixed 24-hour duration.
Orders beyond the simulation end stay open with NULL delivered_at. No partial
deliveries, supplier failures, product substitutions or price inflation are modeled.

At DST fall-back the repeated 01:00 expiry is the standard-time occurrence;
at spring-forward a nonexistent 02:00 adjustment shifts to 03:00. Deliveries,
decisions and trading hours are outside these ambiguous/nonexistent hours.

The baseline uses the trailing 14 *completed* days of fulfilled ingredient
consumption (all available days during warm-up); zero days uses the engineering
prior. Reorder if on_hand + on_order < mean*(lead+1). Target is
mean*min(lead+2,shelf_life). Positive purchase quantities round up to package size
and MOQ; otherwise zero. Outstanding supply is netted once. The policy does not
forecast expiry by lot and can overbuy or underorder; that is a deliberate baseline
for backtesting, not an optimal recommendation. Package rounding can exceed the
shelf-life target. Fixed shelf lives make some waste unavoidable under this policy.

## Experiment boundaries

Decision features reflect the 05:00 state after deliveries but before its own
purchase order. Market features are equal category means of latest previously
available synthetic indices for menu products using the ingredient. Equal product
category contributions avoid adding heterogeneous recipe units. Sentiment is the
branch's prior 14-day mean of positive=1, negative=-1, mixed/neutral=0, with zero
and review_count=0 for no reviews. Future stockout labels indicate a causal
ingredient-shortage event during the configured evaluation horizon under the
actual historical policy. They are policy-dependent outcomes, not counterfactual
optimal purchases. Terminal incomplete windows have NULL targets and
label_observed=0. No oracle purchase labels are generated.

ML tables are deliberate denormalized experiment snapshots. Feature allowlists
are in docs/feature_manifest.json: rating is excluded from sentiment input because
it contributes to labels; baseline_purchase_qty is the reference restock target,
not an input to that task. Target and publication metadata must not be fed to ML.
Chronological splits use 70/15/15; any train/validation outcome window reaching
the following split is marked purged. Filter label_observed=1 for evaluation,
exclude split=purged, and fit transformations on train only. Inventory histories
are generated continuously across splits; this represents deployment with known
past records. No final predictive model is trained. Trend targets are next-seven-
day fulfilled category units; their features contain only the prior weekly index.

Limitations: two independently sourced datasets cannot establish a measured
causal link between real consumer sentiment, trends and NYC demand. Historical
source distributions are only priors, not validated future business forecasts.
Missing geoMap(1).csv prevents the original six-file completeness criterion from
being met literally; this limitation is explicit and does not block an honest
generator using the available sources.
