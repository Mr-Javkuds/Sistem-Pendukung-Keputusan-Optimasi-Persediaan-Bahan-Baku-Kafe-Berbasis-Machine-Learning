"""Source-conditional demand proposals. Inventory later sets fulfillment."""
import numpy as np
import pandas as pd

def generate(config, tables, sales, rng):
    days = pd.date_range(config['start_date'],config['end_date'])
    exposure = sales[['date','weekday']].drop_duplicates().weekday.value_counts()
    weekday = sales.weekday.value_counts().div(exposure).reindex(range(7)).fillna(1)
    weekday /= weekday.mean()
    mean_branch = sales.store_location.value_counts().mean()
    rows = []
    trends = tables['market_trends']
    for day in days:
        # Demand reacts to a previously published weekly index with a seven-day lag.
        known = trends[pd.to_datetime(trends.week_start) <= day-pd.Timedelta(days=7)]
        interest = known.groupby('category_id').tail(1).set_index('category_id').interest_index
        for branch in tables['branches'].itertuples():
            source = sales[sales.store_location == branch.branch_name]
            scale = len(source)/mean_branch if len(source) else 1
            source = source if len(source) else sales
            seasonal = 1+.10*np.cos(2*np.pi*day.dayofyear/365.25)
            n = rng.poisson(config['mean_daily_transactions_per_branch']*scale*weekday[day.dayofweek]*seasonal)
            weights=[]
            pools=[]
            for product in tables['products'].itertuples():
                pool=source[source.product_type==product.source_product_type_proxy]
                if pool.empty:
                    category=tables['categories'].set_index('category_id').loc[product.category_id,'category_name']
                    pool=source[source.product_category==category]
                if pool.empty:
                    pool=source
                pools.append(pool)
                # Divide source proxy popularity among menu products sharing the proxy.
                repeats=sum(tables['products'].source_product_type_proxy==product.source_product_type_proxy)
                weights.append(len(pool)/repeats*np.exp(.012*(interest[product.category_id]-50)))
            weights=np.asarray(weights)/sum(weights)
            picks=rng.choice(len(pools),n,p=weights)
            hour_counts=source.hour.value_counts(normalize=True).sort_index()
            for pick in picks:
                pool=pools[pick]
                sample=pool.iloc[int(rng.integers(len(pool)))]
                hour=int(rng.choice(hour_counts.index,p=hour_counts.values))
                at=(day+pd.Timedelta(hours=hour,minutes=int(rng.integers(60)),seconds=int(rng.integers(60)))).tz_localize(config['timezone'])
                rows.append((len(rows)+1,branch.branch_id,pick+1,at.isoformat(),
                             max(1,int(sample.transaction_qty)),round(float(sample.unit_price),2)))
    return pd.DataFrame(rows,columns=['demand_id','branch_id','product_id','transaction_at','requested_qty','unit_price_usd']).sort_values(['transaction_at','demand_id']).reset_index(drop=True)
