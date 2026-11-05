# CafeStock Intelligence — synthetic research data

Reproducible Python 3.11+ generator for a fictional three-branch NYC cafe,
2025-11-04 through 2026-11-03. Produces 22 required CSV tables plus the explicit
latent_demand table, PostgreSQL DDL/import, ML feature allowlists and audit reports.
No frontend, API or predictive model is included.

Scope update (2026-11-05): the intended operational sentiment source is regional
social-media discussion about menu items, rather than reviews of the cafe itself.
See [the revised design](docs/sentimen_pasar_menu.md). Existing generated CSVs and
validation reports still describe the original synthetic purchase-review scenario.

## Run

From this directory with Python 3.11 or newer:

```powershell
py -3.11 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe generate.py --audit-only
.venv/Scripts/python.exe generate.py --verify-reproducibility
.venv/Scripts/python.exe -m src.validate
```

Alternatively, `uv venv --python 3.11 .venv` and
`uv pip install --python .venv/Scripts/python.exe -r requirements.txt`.
The execution in this workspace uses the environment at `../.venv`.
Pinned runtime dependencies are in requirements.txt. Generation itself is offline.
Run time and file size scale with configured daily transaction count and dates.
`generate.py --config path/to/config.yaml` overrides the default YAML. Output
locations remain relative to generate.py, independent of your working directory.
The same input bytes, config, seed and dependency versions generate identical CSV
bytes. The generator overwrites its own output and report files; preserve an
experiment copy before changing the configuration.

## Sources and limitations

Input CSV copies were obtained from the Downloads paths supplied with the task.
geoMap(1).csv was not supplied/found: its absence is reported explicitly.
multiTimeline.csv is an additional weekly Central Java source; geoMap.csv is
geographic data. Neither is treated as NYC measurements. The alternative supplied
parquet is unused because the authoritative CSV is available. All source bytes
remain in input/; external sources are not business facts about CafeStock.

See reports/source_audit.md for actual schemas, missing values, encoding, dates,
row counts and duplicate counts; reports/statistical_profile.md for distributions
and documented profiling exclusions. Read docs/assumptions.md before modeling.

## Outputs and experiments

Every output CSV is UTF-8, comma-delimited with a header and deterministic row
order. Empty values are NULL; IDs are stable integers. Currency is USD. All
ingredient quantities use the ingredient's base unit (g, ml, piece). Timestamps
include the NYC timezone offset and account for DST.

Sales analysis must use transaction_items.fulfilled_qty; requested_qty is latent
demand. Transactions include failed attempts. Recipe consumption is only from
fulfilled units. inventory_snapshots reconcile with signed movements, expiry
waste and adjustments. Future purchase orders remain open if their due date falls
after the data period. Reviews reference fulfilled items, inheriting their branch
and product. Trends are explicitly synthetic, including pre-period warm-up weeks.

The reference restock quantity comes from a documented historical ordering rule;
it is not mathematically optimal. Read docs/feature_manifest.json for feature
allowlists and targets. Exclude `split=purged` and require `label_observed=1` for
outcome evaluation. Terminal future windows are censored. Rating must not be
included as a sentiment-model feature. Temporal train/validation/test splits are
provided; do not randomly split time-dependent rows. Template-based synthetic
reviews are unsuitable for claims of real-world NLP accuracy.

## PostgreSQL

Use an empty, dedicated local database (PostgreSQL 18 verified). Run from this
directory because psql client-side COPY paths resolve from the current directory:

```powershell
psql -v ON_ERROR_STOP=1 -d cafestock -f sql/schema.sql -f sql/import.sql
```

To repeat the full import and six negative constraint tests in a disposable
cluster without using an existing database:

```powershell
.venv/Scripts/python.exe verify_postgres.py --pg-bin "C:/Program Files/PostgreSQL/18/bin"
```

This helper binds a temporary server to 127.0.0.1:55440, shuts it down after
verification, and retains its temporary diagnostic directory. Override `--port`
if needed. It requires the local PostgreSQL server binaries, not just a client.

DDL and import each run atomically. Import targets explicit column lists, with
UTF-8 encoding and empty-string NULL. PK/FK/check constraints reject invalid rows.
See docs/data_dictionary.md, docs/erd.md and sql/constraint_checks.sql. Cross-row
recipe, temporal, FEFO and conservation invariants are also checked independently
by Python; the schema alone cannot enforce them all. No production database is
modified. To undo a disposable experiment, discard that database (data loss).

## Verification

reports/validation_report.md contains results over the exported CSVs, including
ledger and per-item recipe reconstruction, FEFO expiry, point-in-time features,
supplier lead times, no source-review copying, targets, distributions and keys.
reports/reproducibility_report.md compares all output CSV bytes across two fresh
generations. reports/generation_manifest.json records input/output SHA-256,
config and runtime versions. reports/postgres_verification.md records actual
database import and constraint checks; no model accuracy metrics are claimed.
