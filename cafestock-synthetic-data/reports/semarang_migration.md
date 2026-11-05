# Semarang + Instagram synthetic dataset migration

Requested scope: menu discussion in Semarang, synthetic Instagram data, no cafe
reviews. No actual Instagram scraping was performed and no real accounts/post
URLs were invented. This migration does not claim actual menu popularity.

## Current dataset

- 4 market regions: Semarang city, Semarang Tengah, Semarang Selatan, Banyumanik.
- 3 fictional CafeStock branches, timezone Asia/Jakarta, currency IDR.
- 6,612 original synthetic Indonesian Instagram-like captions and menu mentions.
- 13,224 menu aspect labels (taste/value); 508 monthly region/menu signal rows.
- 321 posts retain unknown location and do not contribute to regional signals.
- 49 sentiment rows have future collection batches and split=pending.
- 98,128 synthetic transaction attempts; 10,950 ingredient decision snapshots.
- 26 output CSVs, all explicitly synthetic or derived from the simulation.

These counts correspond to the checked-in default config/seed. Regeneration with
another config can change the counts; generation_manifest.json is authoritative.

## Removed from the active version

- input/raw_yelp_review_data.csv
- input/ratings_and_sentiments.csv
- input/sentiments_by_shop.csv
- output/customer_reviews.csv
- output/review_aspects.csv
- src/generate_reviews.py

The Downloads originals outside this project were not modified. This is a normal
versioned change; existing Git history is not rewritten. The initial specification
and example proposal remain historical references, not active data requirements.

## Replacement links

social_posts -> menu_mentions -> products -> recipes -> recipe_ingredients ->
ingredients; social_posts.region_id and branches.region_id determine the eligible
local market. Branch features include its district plus city-wide discussion,
not purchases by the authors and not discussion from other districts.

Collection is monthly at 07:00 on the first day of the next month. A 05:00 stock
decision cannot use the batch collected at 07:00 that same day. Feature metadata
tracks publication and availability. Missing data has a separate indicator.

## Verification

Full exported-table validation and independent feature reconstruction results:
validation_report.md. Reproducibility: 26/26 CSVs byte-identical across two fresh
generations. PostgreSQL import: all 26 tables imported in a disposable cluster,
row counts matched; six invalid relational/operational mutations were rejected.

Four targeted unittest cases passed: monthly collection timing; independence from
purchase records; batch gating with district/unknown-location isolation; and
invariance of earlier features when only a future batch is changed.

This prepares experiments, not trained final models. Template-based sentiment
accuracy and market effects still require honest evaluation and cannot establish
real-world Instagram performance.
