"""External transaction patterns only; no Yelp or cafe-review dependency."""
import json
import pandas as pd

def probabilities(series):
    return {str(k):float(v) for k,v in series.value_counts(normalize=True).sort_index().items()}

def profile(root,frames):
    sales=frames['coffee-shop-sales-revenue.csv'].copy()
    sales['date']=pd.to_datetime(sales.transaction_date)
    sales['hour']=pd.to_datetime(sales.transaction_time,format='%H:%M:%S').dt.hour
    sales['weekday']=sales.date.dt.dayofweek
    p={'sales_rows':len(sales),'hour':probabilities(sales.hour),'weekday':probabilities(sales.weekday),
       'quantity':probabilities(sales.transaction_qty),'category':probabilities(sales.product_category),
       'source_branch':probabilities(sales.store_location),
       'source_price_usd_quantiles':sales.unit_price.quantile([0,.1,.5,.9,1]).to_dict(),
       'invalid_quantity_count':int(sales.transaction_qty.le(0).sum()),
       'invalid_price_count':int(sales.unit_price.le(0).sum())}
    (root/'reports'/'source_profile.json').write_text(json.dumps(p,indent=2),encoding='utf-8')
    (root/'reports'/'statistical_profile.md').write_text(
        '# Statistical profile\n\n```json\n'+json.dumps(p,indent=2)+'\n```\n\n'
        'Only transaction timing, relative popularity and conditional quantity patterns are transferred. '
        'Semarang branch-to-source-location mappings are explicit statistical proxies, not real identities. '
        'Synthetic IDR menu prices and ingredient costs are invented local assumptions; source USD prices '
        'are neither converted nor merged into IDR distributions. Instagram captions, labels and posting '
        'frequency are entirely synthetic assumptions, independent of Yelp and CafeStock transactions.\n',encoding='utf-8')
    return sales,p
