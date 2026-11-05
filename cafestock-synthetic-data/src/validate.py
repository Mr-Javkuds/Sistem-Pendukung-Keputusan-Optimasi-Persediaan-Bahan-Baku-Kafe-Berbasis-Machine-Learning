"""Independent checks over exported tables; never mutate or repair records."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from .schema import PRIMARY,FKS,UNIQUE,ORDER,is_nullable

def load(root):
    return {name:pd.read_csv(root/'output'/f'{name}.csv',keep_default_na=True) for name in ORDER}

def validate(root,tables,config,source_profile=None):
    checks=[]
    def check(name,condition,detail=''):
        checks.append((name,bool(condition),str(detail)))
    t=tables
    for name,frame in t.items():
        if name not in PRIMARY: continue
        pk=PRIMARY[name]
        check(name+' primary key',frame[pk].notna().all() and frame[pk].is_unique)
        for col in frame:
            if not is_nullable(name,col): check(name+' required '+col,frame[col].notna().all())
        for cols in UNIQUE.get(name,[]): check(name+' unique '+','.join(cols),not frame.duplicated(cols).any())
        for col,parent in FKS.get(name,{}).items():
            check(name+' FK '+col,frame[col].dropna().isin(t[parent][PRIMARY[parent]]).all())
        for col in frame:
            if col.endswith('_at') or col=='label_window_end':
                dates=pd.to_datetime(frame[col],utc=True,errors='coerce')
                check(name+' timestamp '+col,dates.notna().sum()==frame[col].notna().sum())
                if col in ('transaction_at','published_at','movement_at','decision_at','event_at','ordered_at'):
                    low=pd.Timestamp(config['start_date']).tz_localize(config['timezone'])
                    high=(pd.Timestamp(config['end_date'])+pd.Timedelta(days=1)).tz_localize(config['timezone'])
                    check(name+' period '+col,((dates.dropna()>=low)&(dates.dropna()<high)).all())
    s=t['inventory_snapshots']; m=t['inventory_movements'].copy()
    check('Nonnegative daily inventory',s[['opening_stock','closing_stock']].ge(-1e-6).all().all())
    residual=s.closing_stock-(s.opening_stock+s.receipts-s.consumption-s.waste+s.adjustments)
    check('Daily conservation',residual.abs().max()<1e-5,f'max residual={residual.abs().max():.8g}')
    sorted_s=s.sort_values(['branch_id','ingredient_id','date'])
    previous=sorted_s.groupby(['branch_id','ingredient_id']).closing_stock.shift()
    check('Consecutive daily continuity',np.allclose(sorted_s.loc[previous.notna(),'opening_stock'],previous.dropna(),atol=1e-5))
    m['time']=pd.to_datetime(m.movement_at,utc=True)
    running=m.sort_values(['time','movement_id']).groupby(['branch_id','ingredient_id']).quantity.cumsum()
    check('No negative stock at any movement',running.min()>=-1e-5,f'min={running.min()}')
    # Reconstruct expiring lots independently from the signed ledger.
    lot_errors=[]
    for (branch,ingredient),group in m.groupby(['branch_id','ingredient_id']):
        lots=[]
        shelf=int(t['ingredients'].set_index('ingredient_id').loc[ingredient,'shelf_life_days'])
        for r in group.sort_values(['time','movement_id']).itertuples():
            day=pd.Timestamp(r.movement_at[:10])
            if r.movement_type in ('opening','receipt'):
                lots.append([day+pd.Timedelta(days=shelf),r.quantity])
            else:
                if r.movement_type=='waste':
                    expiring=sum(q for expiry,q in lots if expiry<=day)
                    if abs(expiring+r.quantity)>1e-5: lot_errors.append(r.movement_id)
                elif any(expiry<=day and q>1e-6 for expiry,q in lots): lot_errors.append(r.movement_id)
                remaining=-r.quantity
                for lot in sorted(lots,key=lambda v:v[0]):
                    used=min(lot[1],remaining); lot[1]-=used; remaining-=used
                lots=[lot for lot in lots if lot[1]>1e-6]
                if remaining>1e-5: lot_errors.append(r.movement_id)
    check('Independent FEFO expiry and lot reconstruction',not lot_errors,str(lot_errors[:5]))
    m['date']=m.movement_at.str[:10]
    totals=m.groupby(['branch_id','ingredient_id','date','movement_type']).quantity.sum().unstack(fill_value=0)
    reconstructed=s.set_index(['branch_id','ingredient_id','date']).join(totals,rsuffix='_movement').fillna(0)
    check('Snapshot closing equals cumulative ledger',np.allclose(
        s.groupby(['branch_id','ingredient_id']).closing_stock.last().sort_index(),
        m.groupby(['branch_id','ingredient_id']).quantity.sum().sort_index(),atol=1e-5))
    for field,kind,sign in [('receipts','receipt',1),('consumption','consumption',-1),('waste','waste',-1),('adjustments','adjustment',1)]:
        lhs=s.set_index(['branch_id','ingredient_id','date'])[field]
        rhs=m[m.movement_type==kind].groupby(['branch_id','ingredient_id','date']).quantity.sum()*sign
        check('Ledger daily '+field,np.allclose(lhs,rhs.reindex(lhs.index,fill_value=0),atol=1e-5))
    items=t['transaction_items']; tx=t['transactions'].set_index('transaction_id')
    ing=t['ingredients'].set_index('ingredient_id'); recipes=t['recipe_ingredients']
    check('Every product has one recipe',set(t['products'].product_id)==set(t['recipes'].product_id) and t['recipes'].product_id.is_unique)
    check('Recipe positive valid units',recipes.quantity.gt(0).all() and ing.unit.isin(['g','ml','piece']).all())
    check('Fulfilled quantity bounded',items.fulfilled_qty.ge(0).all() and items.fulfilled_qty.le(items.requested_qty).all())
    expected=items.merge(t['recipes'][['product_id','recipe_id']],on='product_id').merge(recipes,on='recipe_id')
    expected['units']=expected.fulfilled_qty*expected.quantity
    expected=expected.groupby(['transaction_item_id','ingredient_id']).units.sum()
    actual=-m[m.movement_type=='consumption'].groupby(['transaction_item_id','ingredient_id']).quantity.sum()
    check('All recipe consumption reconciles per transaction item',np.allclose(expected,actual.reindex(expected.index,fill_value=0),atol=1e-5) and actual.index.isin(expected.index).all())
    movement_items=m[m.transaction_item_id.notna()]
    check('Consumption movement branch matches transaction',movement_items.branch_id.eq(movement_items.transaction_item_id.map(items.set_index('transaction_item_id').transaction_id).map(tx.branch_id)).all())
    demand=t['latent_demand'].set_index('demand_id')
    check('Latent demand and transaction item identities',len(demand)==len(items) and
          items.product_id.eq(items.demand_id.map(demand.product_id)).all() and
          items.requested_qty.eq(items.demand_id.map(demand.requested_qty)).all() and
          items.transaction_id.map(tx.branch_id).eq(items.demand_id.map(demand.branch_id)).all())
    po=t['purchase_orders'].set_index('purchase_order_id'); poi=t['purchase_order_items']
    lead=(pd.to_datetime(po.expected_delivery_at,utc=True)-pd.to_datetime(po.ordered_at,utc=True)).dt.total_seconds()/3600
    # Civil calendar lead time accounts for DST (one-hour offset) and 04:00 vs 05:00.
    expected_dates=po.ordered_at.str[:10].map(pd.Timestamp)+pd.to_timedelta(po.supplier_id.map(t['suppliers'].set_index('supplier_id').lead_time_days),unit='D')
    check('Supplier civil-date lead times',po.expected_delivery_at.str[:10].eq(expected_dates.dt.strftime('%Y-%m-%d')).all())
    delivered=po[po.status=='delivered']
    check('Delivery timestamps match planned schedule',delivered.delivered_at.eq(delivered.expected_delivery_at).all())
    check('Order supplier matches ingredient supplier',poi.purchase_order_id.map(po.supplier_id).eq(poi.ingredient_id.map(ing.supplier_id)).all())
    packages=poi.ingredient_id.map(ing.package_size)
    check('MOQ and package constraints',poi.quantity.ge(poi.ingredient_id.map(ing.minimum_order_qty)).all() and np.allclose(poi.quantity/packages,np.round(poi.quantity/packages)))
    receipts=m[m.movement_type=='receipt']
    actual_receipts=receipts.groupby('purchase_order_item_id').quantity.sum()
    delivered_items=poi[poi.purchase_order_id.isin(delivered.index)].set_index('purchase_order_item_id')
    check('Receipts equal delivered purchase quantities',set(actual_receipts.index)==set(delivered_items.index) and np.allclose(delivered_items.quantity,actual_receipts.reindex(delivered_items.index)))
    check('Receipt branch and ingredient match purchase order',receipts.branch_id.eq(receipts.purchase_order_item_id.map(poi.set_index('purchase_order_item_id').purchase_order_id).map(po.branch_id)).all() and receipts.ingredient_id.eq(receipts.purchase_order_item_id.map(poi.set_index('purchase_order_item_id').ingredient_id)).all())
    waste=t['waste_records'].set_index('movement_id')
    wm=m[m.movement_type=='waste'].set_index('movement_id')
    check('Waste records reconcile ledger',set(waste.index)==set(wm.index) and np.allclose(waste.quantity,-wm.quantity.reindex(waste.index)))
    itemmap=items.set_index('transaction_item_id')
    posts=t['social_posts']; mentions=t['menu_mentions']; aspects=t['menu_aspects']
    check('All branches are Semarang WIB',t['branches'].timezone.eq('Asia/Jakarta').all() and t['regions'].city.eq('Semarang').all())
    check('No cafe-review tables or source files',not any(n in t for n in ['customer_reviews','review_aspects']) and
          not any((root/'input'/n).exists() for n in ['raw_yelp_review_data.csv','ratings_and_sentiments.csv','sentiments_by_shop.csv']) and
          not any((root/'output'/n).exists() for n in ['customer_reviews.csv','review_aspects.csv']))
    check('Social posts are explicitly synthetic Instagram',posts.platform.eq('instagram').all() and posts.provenance.eq('synthetic').all() and posts.source_post_key.str.startswith('SIM-IG-SMG-').all())
    check('No fabricated real Instagram URL or account',posts.source_url.isna().all() and not any('account' in c or 'username' in c for c in posts))
    check('No purchase, cafe, or rating link in public discussion',not any(c in posts or c in mentions for c in ['transaction_item_id','transaction_id','branch_id','rating','review_text']) and not posts.content_text.str.contains('CafeStock',case=False,regex=False).any())
    check('Indonesian menu discussion provenance',posts.language.eq('id').all() and mentions.label_provenance.eq('synthetic_rule').all())
    check('Location uncertainty explicitly represented',posts.loc[posts.region_id.isna(),'location_evidence'].eq('unknown').all() and posts.loc[posts.region_id.notna(),'location_evidence'].eq('synthetic_scenario').all())
    pub=pd.to_datetime(posts.published_at,utc=True); collected=pd.to_datetime(posts.collected_at,utc=True)
    check('Collection follows publication',(collected>=pub).all())
    expected_collection=posts.published_at.str[:7].map(lambda v:(pd.Timestamp(v+'-01')+pd.offsets.MonthBegin(1)+pd.Timedelta(hours=7)).tz_localize(config['timezone']).isoformat())
    check('Monthly Instagram collection schedule',posts.collected_at.eq(expected_collection).all())
    check('Menu names occur in corresponding caption',all(t['products'].set_index('product_id').loc[r.product_id,'product_name'] in posts.set_index('post_id').loc[r.post_id,'content_text'] for r in mentions.itertuples()))
    aspect_sets=aspects.groupby('mention_id').sentiment_label.agg(set)
    check('Menu sentiment ground truth consistent with aspects',all(
        aspect_sets.loc[r.mention_id]==({'positive','negative'} if r.sentiment_label=='mixed' else {r.sentiment_label}) for r in mentions.itertuples()))
    check('All four menu sentiment classes available',set(mentions.sentiment_label)=={'positive','neutral','negative','mixed'})
    social_rows=mentions.merge(posts,on='post_id')
    social_rows['period_start']=social_rows.published_at.str[:7]+'-01'
    signals=t['menu_market_signals']
    eligible=social_rows[social_rows.region_id.notna()]
    groups={key:g for key,g in eligible.groupby(['region_id','product_id','period_start'])}
    signal_errors=[]
    for r in signals.itertuples():
        g=groups.get((r.region_id,r.product_id,r.period_start))
        if g is None: signal_errors.append(r.signal_id); continue
        counts=g.sentiment_label.value_counts()
        score=g.sentiment_label.map({'positive':1,'negative':-1,'neutral':0,'mixed':0}).mean()
        valid=(r.post_count==g.post_id.nunique() and abs(r.sentiment_mean-score)<1e-5 and
               r.available_at==g.collected_at.max() and r.source_max_published_at==g.published_at.max() and
               all(getattr(r,k+'_count')==counts.get(k,0) for k in ['positive','neutral','negative','mixed']))
        if not valid: signal_errors.append(r.signal_id)
    check('Monthly region/menu signals independently reconstructed',not signal_errors and len(groups)==len(signals),str(signal_errors[:5]))
    check('Regional signals exclude unknown locations',signals.region_id.notna().all() and set(signals.region_id)<=set(t['regions'].region_id))
    sentiment=t['sentiment_ml_dataset']; postmap=posts.set_index('post_id')
    check('Sentiment training rows retain correct caption and label',sentiment.content_text.eq(sentiment.post_id.map(postmap.content_text)).all() and
          sentiment.sentiment_label.eq(sentiment.mention_id.map(mentions.set_index('mention_id').sentiment_label)).all())
    start=pd.Timestamp(config['start_date']); total=(pd.Timestamp(config['end_date'])-start).days+1
    def expected_split(day):
        fraction=(pd.Timestamp(day)-start).days/total
        if day>config['end_date']: return 'pending'
        return 'train' if fraction<.7 else ('validation' if fraction<.85 else 'test')
    check('Social splits use ingestion time, not publication time',sentiment.split.eq(sentiment.collected_at.str[:10].map(expected_split)).all())
    check('Uncollected terminal batches excluded from training',sentiment.loc[sentiment.collected_at.str[:10]>config['end_date'],'split'].eq('pending').all())
    # Independently reconstruct canonical hashes and time-ordered eligibility.
    import re,unicodedata
    hashes=sentiment.content_text.map(lambda v:hashlib.sha256(re.sub(r'\s+',' ',unicodedata.normalize('NFKC',v).casefold()).strip().encode('utf-8')).hexdigest())
    check('Canonical text fingerprints independently verified',sentiment.text_fingerprint.eq(hashes).all())
    chronological=sentiment.sort_values(['collected_at','post_id','mention_id'],kind='stable')
    seen={}; expected_status={}
    for r in chronological.itertuples():
        if r.split=='pending': expected_status[r.Index]='pending'; continue
        if r.text_fingerprint in seen:
            expected_status[r.Index]='duplicate' if seen[r.text_fingerprint]==r.sentiment_label else 'label_conflict'
        else:
            seen[r.text_fingerprint]=r.sentiment_label; expected_status[r.Index]='eligible'
    check('Earliest-ingestion text eligibility independently verified',sentiment.training_status.eq(sentiment.index.map(expected_status)).all())
    eligible_sentiment=sentiment[sentiment.training_status=='eligible']
    check('No eligible duplicate text within or across ML partitions',eligible_sentiment.text_fingerprint.is_unique)
    check('Pending collection never eligible',not eligible_sentiment.split.eq('pending').any())
    decisions=t['restock_decision_dataset']
    for col in ['market_feature_max_at','social_feature_max_at','social_available_at']:
        mask=decisions[col].notna()
        check('No future feature '+col,(pd.to_datetime(decisions.loc[mask,col],utc=True)<pd.to_datetime(decisions.loc[mask,'decision_at'],utc=True)).all())
    # Recompute features, not merely their declared timestamp metadata.
    social_rows['collected_time']=pd.to_datetime(social_rows.collected_at,utc=True)
    snapshot_index=s.set_index(['branch_id','ingredient_id','date'])
    daily_index=s.assign(date=pd.to_datetime(s.date)).set_index(['branch_id','ingredient_id']).sort_index()
    order_state=poi.merge(po.reset_index(),on='purchase_order_id')
    order_state['ordered_time']=pd.to_datetime(order_state.ordered_at,utc=True)
    order_state['delivered_time']=pd.to_datetime(order_state.delivered_at,utc=True)
    order_groups={key:g for key,g in order_state.groupby(['branch_id','ingredient_id'])}
    social_cache={}
    branch_regions=t['branches'].set_index('branch_id').region_id
    ingredient_products={i:set(g.recipe_id.map(t['recipes'].set_index('recipe_id').product_id))
                         for i,g in t['recipe_ingredients'].groupby('ingredient_id')}
    errors=[]
    for row in decisions.itertuples():
        at=pd.Timestamp(row.decision_at); date=row.decision_at[:10]
        key=(row.branch_id,row.ingredient_id)
        sr=snapshot_index.loc[(*key,date)]
        usable=sr.opening_stock-sr.waste+sr.adjustments+sr.receipts
        history=daily_index.loc[key]
        before=history[(history.date<pd.Timestamp(date))&(history.date>=pd.Timestamp(date)-pd.Timedelta(days=14))]
        cachekey=(row.branch_id,date,tuple(sorted(ingredient_products[row.ingredient_id])))
        if cachekey not in social_cache:
            rr=social_rows[social_rows.region_id.isin([1,branch_regions[row.branch_id]])&
                social_rows.product_id.isin(ingredient_products[row.ingredient_id])&(social_rows.collected_time<at)]
            if len(rr): rr=rr[rr.period_start==rr.period_start.max()]
            social_cache[cachekey]=rr
        rr=social_cache[cachekey]
        outstanding=order_groups.get(key,order_state.iloc[:0])
        outstanding=outstanding[(outstanding.ordered_time<at)&
                                (outstanding.delivered_time.isna()|(outstanding.delivered_time>at))]
        valid=(abs(usable-row.on_hand)<1e-5 and len(before)==row.history_days and
               (not len(before) or abs(before.consumption.mean()-row.mean_daily_consumption_14d)<1e-5) and
               len(rr)==row.social_post_count_latest_month and
               abs((rr.sentiment_label.map({'positive':1,'negative':-1,'neutral':0,'mixed':0}).mean() if len(rr) else 0)-row.menu_sentiment_latest_month)<1e-5 and
               row.social_data_available==int(len(rr)>0) and
               (not len(rr) or (rr.collected_at.max()==row.social_available_at and rr.published_at.max()==row.social_feature_max_at and rr.period_start.max()==row.social_period_start)) and
               abs(outstanding.quantity.sum()-row.on_order)<1e-5)
        if not valid: errors.append(row.decision_id)
    check('Independent historical operational and regional-menu feature reconstruction',not errors,str(errors[:5]))
    observed=decisions.label_observed.eq(1)
    check('Censored targets are NULL',decisions.loc[~observed,'future_stockout_7d'].isna().all() and decisions.loc[observed,'future_stockout_7d'].notna().all())
    ev=t['stockout_events'].copy()
    ev['branch_id']=ev.transaction_item_id.map(itemmap.transaction_id).map(tx.branch_id)
    ev['time']=pd.to_datetime(ev.event_at,utc=True).astype('int64')
    event_groups={key:np.sort(g.time.to_numpy()) for key,g in ev.groupby(['branch_id','ingredient_id'])}
    label_errors=[]; policy_errors=[]; market_errors=[]
    cats=t['recipe_ingredients'].merge(t['recipes'][['recipe_id','product_id']],on='recipe_id').merge(t['products'][['product_id','category_id']],on='product_id')
    category_map=cats.groupby('ingredient_id').category_id.unique().to_dict()
    trend_table=t['market_trends'].copy()
    trend_table['time']=pd.to_datetime(trend_table.available_at,utc=True)
    end=(pd.Timestamp(config['end_date'])+pd.Timedelta(days=1)).tz_localize(config['timezone'])
    for r in decisions.itertuples():
        at=pd.Timestamp(r.decision_at); until=pd.Timestamp(r.label_window_end)
        ns=event_groups.get((r.branch_id,r.ingredient_id),np.array([],dtype='int64'))
        outcome=int(np.searchsorted(ns,until.value)>np.searchsorted(ns,at.value))
        if r.label_observed!=int(until<=end) or (r.label_observed and r.future_stockout_7d!=outcome): label_errors.append(r.decision_id)
        rate=r.mean_daily_consumption_14d
        position=r.on_hand+r.on_order
        need=max(0,rate*min(r.lead_time_days+2,r.shelf_life_days)-position) if position<rate*(r.lead_time_days+1) else 0
        purchase=max(r.minimum_order_qty,np.ceil(need/r.package_size)*r.package_size) if need>0 else 0
        if abs(purchase-r.baseline_purchase_qty)>1e-5: policy_errors.append(r.decision_id)
        known=trend_table[(trend_table.category_id.isin(category_map[r.ingredient_id]))&(trend_table.time<at)].sort_values('time').groupby('category_id').tail(1)
        lagged=trend_table[(trend_table.category_id.isin(category_map[r.ingredient_id]))&(trend_table.time<=at-pd.Timedelta(days=7))].sort_values('time').groupby('category_id').tail(1)
        if abs(known.interest_index.mean()-r.market_interest_latest)>1e-5 or abs(lagged.interest_index.mean()-r.market_interest_lag_1w)>1e-5 or known.available_at.max()!=r.market_feature_max_at: market_errors.append(r.decision_id)
    check('Future stockout labels independently reconstructed',not label_errors,str(label_errors[:5]))
    check('Baseline quantities independently reconstructed',not policy_errors,str(policy_errors[:5]))
    check('Market features independently reconstructed from past only',not market_errors,str(market_errors[:5]))
    risks=t['inventory_risk_ml_dataset']
    check('Risk target agrees with decision evaluation target',risks.target_stockout.fillna(-1).equals(decisions.future_stockout_7d.fillna(-1)))
    aligned=risks.rename(columns={'risk_row_id':'decision_id','target_stockout':'future_stockout_7d'}).drop(columns=['risk_label'])
    check('Risk and restock shared fields exactly synchronized',aligned.equals(decisions))
    manifest=json.loads((root/'docs'/'feature_manifest.json').read_text(encoding='utf-8'))
    check('Risk input allowlist exists and excludes target metadata',set(manifest['risk_features'])<=set(risks.columns) and not set(manifest['risk_features'])&{'target_stockout','risk_label','future_stockout_7d','label_window_end','baseline_purchase_qty','split'})
    check('Training windows purged across split boundaries',all(
        not ((decisions.split==split)&decisions.label_window_end.str[:10].ge(
             (pd.Timestamp(config['start_date'])+pd.Timedelta(days=int(np.ceil(((pd.Timestamp(config['end_date'])-pd.Timestamp(config['start_date'])).days+1)*fraction)))).date().isoformat())).any()
        for split,fraction in [('train',.7),('validation',.85)]))
    trend=t['market_trends']
    check('Trend bounds and provenance',trend.interest_index.between(0,100).all() and trend.provenance.eq('synthetic').all())
    trend_ml=t['trend_ml_dataset']; trend_errors=[]
    prodcat=t['products'].set_index('product_id').category_id
    item_history=items.copy()
    item_history['category_id']=item_history.product_id.map(prodcat)
    item_history['day']=item_history.transaction_id.map(tx.transaction_at).str[:10]
    for r in trend_ml.itertuples():
        at=pd.Timestamp(r.decision_at)
        known=trend_table[(trend_table.category_id==r.category_id)&(trend_table.time<at)].sort_values('time')
        previous=float(known.iloc[-1].interest_index) if len(known) else 50.
        a=at.date().isoformat(); b=(at+pd.DateOffset(days=7)).date().isoformat()
        units=item_history.loc[(item_history.category_id==r.category_id)&(item_history.day>=a)&(item_history.day<b),'fulfilled_qty'].sum()
        if abs(previous-r.interest_lag_1w)>1e-5 or (r.label_observed and r.target_fulfilled_units_next_7d!=units): trend_errors.append(r.trend_row_id)
    check('Trend features and targets independently reconstructed',not trend_errors,str(trend_errors[:5]))
    nonnull=trend_ml.feature_max_at.notna()
    check('Trend features precede decisions',(pd.to_datetime(trend_ml.loc[nonnull,'feature_max_at'],utc=True)<pd.to_datetime(trend_ml.loc[nonnull,'decision_at'],utc=True)).all())
    check('Trend terminal targets censored',trend_ml.loc[trend_ml.label_observed.eq(0),'target_fulfilled_units_next_7d'].isna().all())
    check('Semarang trend region',trend.region_id.eq(1).all())
    check('All decision features finite',np.isfinite(decisions.select_dtypes(include='number').drop(columns=['future_stockout_7d']).to_numpy(dtype=float)).all())
    comparisons={}
    if source_profile:
        genhours=pd.to_datetime(tx.transaction_at,utc=True).dt.tz_convert(config['timezone']).dt.hour.value_counts(normalize=True)
        src=pd.Series({int(k):v for k,v in source_profile['hour'].items()})
        delta=(genhours.reindex(range(24),fill_value=0)-src.reindex(range(24),fill_value=0)).abs().max()
        check('Hourly source distribution plausibility',delta<.08,f'max absolute probability difference={delta:.5f}')
        comparisons['hourly_max_probability_difference']=float(delta)
        actual_labels=mentions.sentiment_label.value_counts(normalize=True)
        assumed=pd.Series({'positive':.45,'neutral':.20,'negative':.20,'mixed':.15})
        difference=(actual_labels.reindex(assumed.index,fill_value=0)-assumed).abs().max()
        tolerance=max(.08,4/np.sqrt(max(1,len(mentions))))
        check('Synthetic sentiment distribution follows explicit assumptions',difference<tolerance,f'max difference={difference:.5f}; tolerance={tolerance:.5f}')
        comparisons.update(sentiment_assumptions=assumed.to_dict(),sentiment_generated=actual_labels.to_dict(),
            quantity_source=source_profile['quantity'],quantity_synthetic=items.requested_qty.value_counts(normalize=True).to_dict(),
            source_price_usd_quantiles=source_profile['source_price_usd_quantiles'],synthetic_price_idr_quantiles=items.unit_price_idr.quantile([0,.1,.5,.9,1]).to_dict(),
            source_category_probabilities=source_profile['category'],
            synthetic_product_counts=items.product_id.value_counts().to_dict())
    summary={'table_rows':{n:len(f) for n,f in t.items()},'requested_units':int(items.requested_qty.sum()),
             'fulfilled_units':int(items.fulfilled_qty.sum()),'unfulfilled_units':int((items.requested_qty-items.fulfilled_qty).sum()),
             'sentiment_counts':mentions.sentiment_label.value_counts().to_dict(),
             'unknown_location_posts':int(posts.region_id.isna().sum()),
             'social_pending_rows':int(sentiment.split.eq('pending').sum()),
             'stockout_target_counts':decisions.future_stockout_7d.value_counts(dropna=False).astype(str).to_dict()}
    # NaN keys need a JSON-safe representation.
    summary['stockout_target_counts']={str(k):v for k,v in summary['stockout_target_counts'].items()}
    report=['# Validation report','',f'{sum(c[1] for c in checks)}/{len(checks)} checks passed.',
            '', '| Check | Result | Detail |','|---|---|---|']
    report += [f'| {n} | {"PASS" if ok else "FAIL"} | {detail} |' for n,ok,detail in checks]
    report += ['','## Generated summary','```json',json.dumps(summary,indent=2),'```',
               '','## Distribution comparisons','```json',json.dumps(comparisons,indent=2),'```',
               '', 'The fictional menu is a subset/proxy of source categories, so exact product/category '
               'marginals are not expected. Seasonal and trend effects intentionally perturb demand. '
               'Instagram-like text is synthetic Indonesian menu discussion, not a cafe review or actual scrape. '
               'USD source prices and synthetic IDR prices are reported separately, never compared as the same currency. '
               'This report contains actual checks, not predictive accuracy or claims of business optimality.']
    (root/'reports'/'validation_report.md').write_text('\n'.join(report),encoding='utf-8')
    (root/'reports'/'validation_results.json').write_text(json.dumps({'checks':checks,'summary':summary,'comparisons':comparisons},indent=2),encoding='utf-8')
    return all(c[1] for c in checks)

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    config=yaml.safe_load((root/'config.yaml').read_text())
    p=json.loads((root/'reports'/'source_profile.json').read_text())
    sys.exit(0 if validate(root,load(root),config,p) else 1)
