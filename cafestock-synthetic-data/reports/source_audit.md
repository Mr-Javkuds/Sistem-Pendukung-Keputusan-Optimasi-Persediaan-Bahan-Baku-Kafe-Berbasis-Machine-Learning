# Source audit

Source observations are external evidence, not CafeStock records. Cafe reviews and all Yelp files were removed from the active project by user request. Instagram discussion is generated synthetically and is not a scraped source.

## coffee-shop-sales-revenue.csv
```json
{
  "status": "present",
  "sha256": "d5a22d9f1137b1c2caae1bdef80f7458c6c90fd09e9aeded6e77b4e00f704884",
  "encoding": "utf-8-sig",
  "delimiter": "|",
  "metadata_lines": 0,
  "rows": 149116,
  "duplicates": 0,
  "columns": {
    "transaction_id": {
      "dtype": "int64",
      "missing": 0,
      "unique": 149116
    },
    "transaction_date": {
      "dtype": "object",
      "missing": 0,
      "unique": 181
    },
    "transaction_time": {
      "dtype": "object",
      "missing": 0,
      "unique": 25762
    },
    "transaction_qty": {
      "dtype": "int64",
      "missing": 0,
      "unique": 6
    },
    "store_id": {
      "dtype": "int64",
      "missing": 0,
      "unique": 3
    },
    "store_location": {
      "dtype": "object",
      "missing": 0,
      "unique": 3
    },
    "product_id": {
      "dtype": "int64",
      "missing": 0,
      "unique": 80
    },
    "unit_price": {
      "dtype": "float64",
      "missing": 0,
      "unique": 41
    },
    "product_category": {
      "dtype": "object",
      "missing": 0,
      "unique": 9
    },
    "product_type": {
      "dtype": "object",
      "missing": 0,
      "unique": 29
    },
    "product_detail": {
      "dtype": "object",
      "missing": 0,
      "unique": 80
    }
  },
  "transaction_date_range": [
    "2023-01-01 00:00:00",
    "2023-06-30 00:00:00"
  ]
}
```

## geoMap.csv
```json
{
  "status": "present",
  "sha256": "6f20fae326c41f94e8bc04e81e04d44a550a5843c223dfc174bf94e667634766",
  "encoding": "utf-8-sig",
  "delimiter": ",",
  "metadata_lines": 2,
  "rows": 67,
  "duplicates": 0,
  "columns": {
    "Kota": {
      "dtype": "object",
      "missing": 0,
      "unique": 67
    },
    "matcha: (04/11/25 - 04/11/26)": {
      "dtype": "float64",
      "missing": 17,
      "unique": 32
    }
  },
  "format": "Geographic interest by city; not a historical time series; Indonesian scope."
}
```

## multiTimeline.csv
```json
{
  "status": "present",
  "sha256": "c3d8b5a406d20abd5b02a8e6086d0b6ddf6bb28ff6ae072a1d22341c5eaea0b8",
  "encoding": "utf-8-sig",
  "delimiter": ",",
  "metadata_lines": 2,
  "rows": 53,
  "duplicates": 0,
  "columns": {
    "Minggu": {
      "dtype": "object",
      "missing": 0,
      "unique": 53
    },
    "matcha: (Jawa Tengah)": {
      "dtype": "int64",
      "missing": 0,
      "unique": 33
    }
  },
  "format": "Weekly matcha interest, Central Java; contextual source, not Semarang city measurements.",
  "Minggu_range": [
    "2025-11-02 00:00:00",
    "2026-11-01 00:00:00"
  ]
}
```
