"""Point-in-time features with explicit, separately named future evaluation targets."""
import numpy as np
import pandas as pd

def generate(config,tables):
    decisions=tables.pop('decisions_internal').copy()
    tx=tables['transactions'].set_index('transaction_id')
    items=tables['transaction_items'].set_index('transaction_item_id')
    reviews=tables['customer_reviews'].copy()
    reviews['branch_id']=reviews.transaction_item_id.map(items.transaction_id).map(tx.branch_id)
    reviews['time']=pd.to_datetime(reviews.review_at,utc=True)
    reviews['score']=reviews.sentiment_label.map({'positive':1,'neutral':0,'negative':-1,'mixed':0})
    trends=tables['market_trends'].copy()
    trends['time']=pd.to_datetime(trends.available_at,utc=True)
    # Recipe-weighted mean of historical category interest; units never mixed in the weights.
    # Equal product contributions avoid adding grams to millilitres.
    product_categories=tables['products'].set_index('product_id').category_id
    ingredient_categories={int(i): sorted(set(g.recipe_id.map(product_categories)))
                           for i,g in tables['recipe_ingredients'].groupby('ingredient_id')}
    events=tables['stockout_events'].copy()
    events['branch_id']=events.transaction_item_id.map(items.transaction_id).map(tx.branch_id)
    events['time']=pd.to_datetime(events.event_at,utc=True)
    end_exclusive=(pd.Timestamp(config['end_date'])+pd.Timedelta(days=1)).tz_localize(config['timezone'])
    features=[]
    horizon=config['evaluation_horizon_days']
    # Pre-index small daily point-in-time groups to keep generation straightforward.
    for row in decisions.itertuples():
        at=pd.Timestamp(row.decision_at)
        past_reviews=reviews[(reviews.branch_id==row.branch_id)&(reviews.time<at)&
                             (reviews.time>=at-pd.Timedelta(days=14))]
        cats=ingredient_categories[row.ingredient_id]
        known=trends[(trends.category_id.isin(cats))&(trends.time<at)]
        latest=known.sort_values('time').groupby('category_id').tail(1)
        future_end=at+pd.DateOffset(days=horizon)
        complete=future_end<=end_exclusive
        future_events=events[(events.branch_id==row.branch_id)&(events.ingredient_id==row.ingredient_id)&
                             (events.time>=at)&(events.time<future_end)]
        features.append((float(latest.interest_index.mean()),latest.available_at.max(),
                         len(past_reviews),float(past_reviews.score.mean()) if len(past_reviews) else 0.,
                         past_reviews.review_at.max() if len(past_reviews) else None,
                         future_end.isoformat(),int(len(future_events)>0) if complete else None,
                         int(complete)))
    for j,col in enumerate(['market_interest_latest','market_feature_max_at','review_count_14d',
                           'sentiment_mean_14d','sentiment_feature_max_at','label_window_end',
                           'future_stockout_7d','label_observed']):
        decisions[col]=[f[j] for f in features]
    decisions['future_stockout_7d']=decisions.future_stockout_7d.astype('Int64')
    decisions['split']=decisions.decision_at.str[:10].map(lambda d: temporal_split(d,config))
    # Targets and metadata are explicitly excluded by the exported feature manifest.
    tables['restock_decision_dataset']=decisions
    risk=decisions.copy().rename(columns={'decision_id':'risk_row_id','future_stockout_7d':'target_stockout'})
    risk['risk_label']=risk.target_stockout.map({0:'no_stockout',1:'stockout'})
    tables['inventory_risk_ml_dataset']=risk
    sentiment=reviews[['review_id','review_text','sentiment_label','rating','review_at']].copy()
    sentiment.insert(0,'sentiment_row_id',range(1,len(sentiment)+1))
    sentiment['split']=sentiment.review_at.str[:10].map(lambda d: temporal_split(d,config))
    tables['sentiment_ml_dataset']=sentiment
    trend_rows=[]
    # Calendar-day bins in NYC; label is next week's fulfilled units, not a forecast model.
    sale_items=tables['transaction_items'].copy()
    sale_items['date']=sale_items.transaction_id.map(tx.transaction_at).str[:10]
    sale_items['category_id']=sale_items.product_id.map(product_categories)
    for trend in tables['market_trends'].itertuples():
        if trend.week_start<config['start_date']:
            continue
        at=pd.Timestamp(trend.available_at)
        previous=trends[(trends.category_id==trend.category_id)&(trends.time<at)]
        a=at.date().isoformat(); b=(at+pd.DateOffset(days=7)).date().isoformat()
        complete=(at+pd.DateOffset(days=7))<=end_exclusive
        units=sale_items.loc[(sale_items.category_id==trend.category_id)&(sale_items.date>=a)&(sale_items.date<b),'fulfilled_qty'].sum()
        trend_rows.append((len(trend_rows)+1,trend.category_id,trend.available_at,
                           float(previous.iloc[-1].interest_index) if len(previous) else 50,
                           previous.iloc[-1].available_at if len(previous) else None,
                           int(units) if complete else None,int(complete),temporal_split(a,config)))
    tables['trend_ml_dataset']=pd.DataFrame(trend_rows,columns=['trend_row_id','category_id','decision_at',
        'interest_lag_1w','feature_max_at','target_fulfilled_units_next_7d','label_observed','split'])
    tables['trend_ml_dataset']['target_fulfilled_units_next_7d']=tables['trend_ml_dataset'].target_fulfilled_units_next_7d.astype('Int64')

def temporal_split(day,config):
    start,end=pd.Timestamp(config['start_date']),pd.Timestamp(config['end_date'])
    fraction=(pd.Timestamp(day)-start).days/max(1,(end-start).days+1)
    return 'train' if fraction<.7 else ('validation' if fraction<.85 else 'test')
