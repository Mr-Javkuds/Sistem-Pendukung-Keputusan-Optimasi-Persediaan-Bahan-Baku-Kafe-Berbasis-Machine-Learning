"""Point-in-time menu/region/month signals, without cafe reviews or purchase links."""
import numpy as np
import pandas as pd
from .cleaning import mark_sentiment_eligibility

def temporal_split(day,config):
    start,end=pd.Timestamp(config['start_date']),pd.Timestamp(config['end_date'])
    if pd.Timestamp(day)>end: return 'pending'
    fraction=(pd.Timestamp(day)-start).days/max(1,(end-start).days+1)
    return 'train' if fraction<.7 else ('validation' if fraction<.85 else 'test')

def generate(config,tables):
    decisions=tables.pop('decisions_internal').copy()
    tx=tables['transactions'].set_index('transaction_id')
    items=tables['transaction_items'].set_index('transaction_item_id')
    trends=tables['market_trends'].copy()
    trends['time']=pd.to_datetime(trends.available_at,utc=True)
    product_categories=tables['products'].set_index('product_id').category_id
    ingredient_products={int(i):sorted(set(g.recipe_id.map(tables['recipes'].set_index('recipe_id').product_id)))
                         for i,g in tables['recipe_ingredients'].groupby('ingredient_id')}
    ingredient_categories={i:sorted(set(product_categories.loc[ps])) for i,ps in ingredient_products.items()}
    branch_regions=tables['branches'].set_index('branch_id').region_id
    signals=tables['menu_market_signals'].copy()
    signals['time']=pd.to_datetime(signals.available_at,utc=True)
    events=tables['stockout_events'].copy()
    events['branch_id']=events.transaction_item_id.map(items.transaction_id).map(tx.branch_id)
    events['time']=pd.to_datetime(events.event_at,utc=True)
    event_groups={key:np.sort(g.time.astype('int64').to_numpy()) for key,g in events.groupby(['branch_id','ingredient_id'])}
    end=(pd.Timestamp(config['end_date'])+pd.Timedelta(days=1)).tz_localize(config['timezone'])
    features=[]; social_cache={}
    for row in decisions.itertuples():
        at=pd.Timestamp(row.decision_at); cats=ingredient_categories[row.ingredient_id]
        known=trends[(trends.category_id.isin(cats))&(trends.time<at)]
        latest=known.sort_values('time').groupby('category_id').tail(1)
        lagged=known[known.time<=at-pd.Timedelta(days=7)].sort_values('time').groupby('category_id').tail(1)
        cachekey=(at.strftime('%Y-%m-%d'),int(branch_regions[row.branch_id]),tuple(ingredient_products[row.ingredient_id]))
        if cachekey not in social_cache:
            available=signals[(signals.region_id.isin([1,branch_regions[row.branch_id]]))&
                              signals.product_id.isin(ingredient_products[row.ingredient_id])&(signals.time<at)]
            period=available.period_start.max() if len(available) else None
            selected=available[available.period_start==period] if period else available
            count=int(selected.post_count.sum())
            score=float((selected.positive_count.sum()-selected.negative_count.sum())/count) if count else 0.
            available_at=selected.available_at.max() if count else None
            social_cache[cachekey]=(count,score,selected.source_max_published_at.max() if count else None,
                available_at,period,int(count>0),(at-pd.Timestamp(available_at)).days if count else 0)
        social=social_cache[cachekey]
        until=at+pd.DateOffset(days=config['evaluation_horizon_days'])
        times=event_groups.get((row.branch_id,row.ingredient_id),np.array([],dtype='int64'))
        outcome=int(np.searchsorted(times,until.value)>np.searchsorted(times,at.value)) if until<=end else None
        features.append((float(latest.interest_index.mean()),float(lagged.interest_index.mean()),
            latest.available_at.max(),*social,until.isoformat(),outcome,int(until<=end)))
    columns=['market_interest_latest','market_interest_lag_1w','market_feature_max_at',
             'social_post_count_latest_month','menu_sentiment_latest_month','social_feature_max_at',
             'social_available_at','social_period_start','social_data_available','social_age_days',
             'label_window_end','future_stockout_7d','label_observed']
    for j,col in enumerate(columns): decisions[col]=[f[j] for f in features]
    decisions['future_stockout_7d']=decisions.future_stockout_7d.astype('Int64')
    decisions['split']=decisions.decision_at.str[:10].map(lambda d:temporal_split(d,config))
    tables['restock_decision_dataset']=decisions
    risk=decisions.rename(columns={'decision_id':'risk_row_id','future_stockout_7d':'target_stockout'}).copy()
    risk['risk_label']=risk.target_stockout.map({0:'no_stockout',1:'stockout'})
    tables['inventory_risk_ml_dataset']=risk
    sentiment=tables['menu_mentions'].merge(tables['social_posts'],on='post_id')
    sentiment=sentiment[['mention_id','post_id','product_id','region_id','published_at','collected_at',
                         'content_text','sentiment_label','label_provenance']].copy()
    sentiment.insert(0,'sentiment_row_id',range(1,len(sentiment)+1))
    sentiment['split']=sentiment.collected_at.str[:10].map(lambda d:temporal_split(d,config))
    tables['sentiment_ml_dataset']=mark_sentiment_eligibility(sentiment)
    sale_items=tables['transaction_items'].copy()
    sale_items['date']=sale_items.transaction_id.map(tx.transaction_at).astype('string').str[:10]
    sale_items['category_id']=sale_items.product_id.map(product_categories)
    trend_rows=[]
    for trend in tables['market_trends'].itertuples():
        if trend.week_start<config['start_date']: continue
        at=pd.Timestamp(trend.available_at)
        previous=trends[(trends.category_id==trend.category_id)&(trends.time<at)]
        a=at.date().isoformat(); b=(at+pd.DateOffset(days=7)).date().isoformat()
        complete=(at+pd.DateOffset(days=7))<=end
        units=sale_items.loc[(sale_items.category_id==trend.category_id)&(sale_items.date>=a)&(sale_items.date<b),'fulfilled_qty'].sum()
        trend_rows.append((len(trend_rows)+1,trend.category_id,trend.available_at,
            float(previous.iloc[-1].interest_index) if len(previous) else 50,
            previous.iloc[-1].available_at if len(previous) else None,int(units) if complete else None,
            int(complete),temporal_split(a,config)))
    tables['trend_ml_dataset']=pd.DataFrame(trend_rows,columns=['trend_row_id','category_id','decision_at',
        'interest_lag_1w','feature_max_at','target_fulfilled_units_next_7d','label_observed','split'])
    tables['trend_ml_dataset']['target_fulfilled_units_next_7d']=tables['trend_ml_dataset'].target_fulfilled_units_next_7d.astype('Int64')
