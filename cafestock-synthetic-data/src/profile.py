"""Only marginal/conditional statistics are transferred across unrelated sources."""
import json
import re
import numpy as np
import pandas as pd

def probabilities(series):
    counts = series.value_counts(normalize=True).sort_index()
    return {str(k): float(v) for k, v in counts.items()}

def profile(root, frames):
    sales = frames['coffee-shop-sales-revenue.csv'].copy()
    sales['date'] = pd.to_datetime(sales.transaction_date)
    sales['hour'] = pd.to_datetime(sales.transaction_time, format='%H:%M:%S').dt.hour
    sales['weekday'] = sales.date.dt.dayofweek
    ratings = frames['ratings_and_sentiments.csv']
    raw = frames['raw_yelp_review_data.csv'].drop_duplicates()
    ratings = ratings.dropna(subset=['review_text','num_rating']).drop_duplicates()
    raw_rating = raw.star_rating.str.extract(r'(\d(?:\.\d)?)')[0].astype(float)
    lengths = raw.full_review_text.fillna('').str.split().str.len()
    p = {'sales_rows': len(sales), 'hour': probabilities(sales.hour),
         'weekday': probabilities(sales.weekday), 'quantity': probabilities(sales.transaction_qty),
         'category': probabilities(sales.product_category),
         'branch': probabilities(sales.store_location), 'rating': probabilities(raw_rating),
         'overall_sent': probabilities(ratings.overall_sent),
         'review_length_quantiles': lengths.quantile([0,.1,.5,.9,1]).to_dict(),
         'aspect_mention_rates': {c.removesuffix('_sent'): float(pd.to_numeric(ratings[c],errors='coerce').fillna(0).ne(0).mean())
                                  for c in ratings if c.endswith('_sent') and c != 'overall_sent'},
         'price_quantiles': sales.unit_price.quantile([0,.1,.5,.9,1]).to_dict(),
         'negative_or_zero_quantity': int(sales.transaction_qty.le(0).sum()),
         'negative_or_zero_price': int(sales.unit_price.le(0).sum())}
    (root/'reports'/'source_profile.json').write_text(json.dumps(p, indent=2), encoding='utf-8')
    (root/'reports'/'statistical_profile.md').write_text(
        '# Statistical profile\n\n```json\n' + json.dumps(p, indent=2) + '\n```\n\n'
        'Profiling excludes 701 exact duplicate raw Yelp rows; raw input bytes are unchanged. '
        'Transformed sentiment rows missing review/rating are excluded, exact duplicates removed, '
        'and numeric aspect parse failures contribute zero to the mention proxy only. '
        'Weekday probabilities are normalized by observed calendar-day exposures during generation. '
        'Branch names map explicitly by matching source location names, never by arbitrary IDs. '
        'Raw review ratings and lengths are used once; transformed Yelp rows and shop aggregates '
        'are overlapping sources and are not pooled as independent reviews. '
        'Aspect integer codes have no supplied codebook: nonzero is used only as a mention proxy, '
        'never as sentiment ground truth.\n', encoding='utf-8')
    return sales, p
