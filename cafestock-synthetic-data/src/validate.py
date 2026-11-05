"""Independent checks over exported tables; never mutate or repair records."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from .schema import PRIMARY,FKS,UNIQUE,ORDER

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
        for cols in UNIQUE.get(name,[]): check(name+' unique '+','.join(cols),not frame.duplicated(cols).any())
        for col,parent in FKS.get(name,{}).items():
            check(name+' FK '+col,frame[col].dropna().isin(t[parent][PRIMARY[parent]]).all())
        for col in frame:
            if col.endswith('_at') or col=='label_window_end':
                dates=pd.to_datetime(frame[col],utc=True,errors='coerce')
                check(name+' timestamp '+col,dates.notna().sum()==frame[col].notna().sum())
                if col in ('transaction_at','review_at','movement_at','decision_at','event_at','ordered_at'):
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
    reviews=t['customer_reviews']; itemmap=items.set_index('transaction_item_id')
    check('Reviews reference fulfilled purchases',reviews.transaction_item_id.map(itemmap.fulfilled_qty).gt(0).all())
    check('Reviews follow purchase', (pd.to_datetime(reviews.review_at,utc=True)>=pd.to_datetime(reviews.transaction_item_id.map(itemmap.transaction_id).map(tx.transaction_at),utc=True)).all())
    labels=reviews.rating.map(lambda r:'positive' if r>=4 else ('negative' if r<=2 else 'neutral'))
    check('Sentiment follows documented rules',reviews.sentiment_label.eq(labels).where(reviews.sentiment_label.ne('mixed'),True).all())
    distinct=t['review_aspects'].groupby('review_id').sentiment_label.nunique()
    check('Mixed reviews contain opposed aspects',reviews.loc[reviews.sentiment_label=='mixed','review_id'].map(distinct).eq(2).all())
    check('No unrelated cafe names',reviews.review_text.str.contains('CafeStock Coffee',regex=False).all())
    # Full source text copying check is exact; no real text is used by the generator.
    from .audit import read_source
    raw,_,_,_=read_source(root/'input'/'raw_yelp_review_data.csv')
    check('No copied source reviews',not reviews.review_text.isin(raw.full_review_text).any())
    decisions=t['restock_decision_dataset']
    for col in ['market_feature_max_at','sentiment_feature_max_at']:
        mask=decisions[col].notna()
        check('No future feature '+col,(pd.to_datetime(decisions.loc[mask,col],utc=True)<pd.to_datetime(decisions.loc[mask,'decision_at'],utc=True)).all())
    # Recompute features, not merely their declared timestamp metadata.
    re=reviews.copy(); re['branch_id']=re.transaction_item_id.map(itemmap.transaction_id).map(tx.branch_id)
    re['time']=pd.to_datetime(re.review_at,utc=True)
    re['score']=re.sentiment_label.map({'positive':1,'negative':-1,'neutral':0,'mixed':0})
    snapshot_index=s.set_index(['branch_id','ingredient_id','date'])
    daily_index=s.assign(date=pd.to_datetime(s.date)).set_index(['branch_id','ingredient_id']).sort_index()
    order_state=poi.merge(po.reset_index(),on='purchase_order_id')
    order_state['ordered_time']=pd.to_datetime(order_state.ordered_at,utc=True)
    order_state['delivered_time']=pd.to_datetime(order_state.delivered_at,utc=True)
    order_groups={key:g for key,g in order_state.groupby(['branch_id','ingredient_id'])}
    review_cache={}
    errors=[]
    for row in decisions.itertuples():
        at=pd.Timestamp(row.decision_at); date=row.decision_at[:10]
        key=(row.branch_id,row.ingredient_id)
        sr=snapshot_index.loc[(*key,date)]
        usable=sr.opening_stock-sr.waste+sr.adjustments+sr.receipts
        history=daily_index.loc[key]
        before=history[(history.date<pd.Timestamp(date))&(history.date>=pd.Timestamp(date)-pd.Timedelta(days=14))]
        cachekey=(row.branch_id,date)
        if cachekey not in review_cache:
            review_cache[cachekey]=re[(re.branch_id==row.branch_id)&(re.time<at)&(re.time>=at-pd.Timedelta(days=14))]
        rr=review_cache[cachekey]
        outstanding=order_groups.get(key,order_state.iloc[:0])
        outstanding=outstanding[(outstanding.ordered_time<at)&
                                (outstanding.delivered_time.isna()|(outstanding.delivered_time>at))]
        valid=(abs(usable-row.on_hand)<1e-5 and len(before)==row.history_days and
               (not len(before) or abs(before.consumption.mean()-row.mean_daily_consumption_14d)<1e-5) and
               len(rr)==row.review_count_14d and abs((rr.score.mean() if len(rr) else 0)-row.sentiment_mean_14d)<1e-5 and
               abs(outstanding.quantity.sum()-row.on_order)<1e-5)
        if not valid: errors.append(row.decision_id)
    check('Independent historical feature reconstruction',not errors,str(errors[:5]))
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
        if abs(known.interest_index.mean()-r.market_interest_latest)>1e-5 or known.available_at.max()!=r.market_feature_max_at: market_errors.append(r.decision_id)
    check('Future stockout labels independently reconstructed',not label_errors,str(label_errors[:5]))
    check('Baseline quantities independently reconstructed',not policy_errors,str(policy_errors[:5]))
    check('Market features independently reconstructed from past only',not market_errors,str(market_errors[:5]))
    risks=t['inventory_risk_ml_dataset']
    check('Risk target agrees with decision evaluation target',risks.target_stockout.fillna(-1).equals(decisions.future_stockout_7d.fillna(-1)))
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
    check('Synthetic review provenance',reviews.label_provenance.eq('synthetic_rule').all())
    check('Review rating bounds',reviews.rating.between(1,5).all())
    check('All decision features finite',np.isfinite(decisions.select_dtypes(include='number').drop(columns=['future_stockout_7d']).to_numpy(dtype=float)).all())
    comparisons={}
    if source_profile:
        genhours=pd.to_datetime(tx.transaction_at,utc=True).dt.tz_convert(config['timezone']).dt.hour.value_counts(normalize=True)
        src=pd.Series({int(k):v for k,v in source_profile['hour'].items()})
        delta=(genhours.reindex(range(24),fill_value=0)-src.reindex(range(24),fill_value=0)).abs().max()
        check('Hourly source distribution plausibility',delta<.08,f'max absolute probability difference={delta:.5f}')
        comparisons['hourly_max_probability_difference']=float(delta)
        rating=reviews.rating.value_counts(normalize=True)
        rsrc=pd.Series({int(float(k)):v for k,v in source_profile['rating'].items()})
        rdelta=(rating.reindex(range(1,6),fill_value=0)-rsrc.reindex(range(1,6),fill_value=0)).abs().max()
        # Finite-sample tolerance, rather than tuning to a desired success percentage.
        tolerance=max(.08,4/np.sqrt(max(1,len(reviews))))
        check('Rating source distribution plausibility',rdelta<tolerance,f'max difference={rdelta:.5f}; tolerance={tolerance:.5f}')
        comparisons.update(rating_source=rsrc.to_dict(),rating_synthetic=rating.to_dict(),
            quantity_source=source_profile['quantity'],quantity_synthetic=items.requested_qty.value_counts(normalize=True).to_dict(),
            source_price_quantiles=source_profile['price_quantiles'],synthetic_price_quantiles=items.unit_price_usd.quantile([0,.1,.5,.9,1]).to_dict(),
            source_review_length_quantiles=source_profile['review_length_quantiles'],
            synthetic_review_length_quantiles=reviews.review_text.str.split().str.len().quantile([0,.1,.5,.9,1]).to_dict(),
            source_category_probabilities=source_profile['category'],
            synthetic_product_counts=items.product_id.value_counts().to_dict())
    summary={'table_rows':{n:len(f) for n,f in t.items()},'requested_units':int(items.requested_qty.sum()),
             'fulfilled_units':int(items.fulfilled_qty.sum()),'unfulfilled_units':int((items.requested_qty-items.fulfilled_qty).sum()),
             'sentiment_counts':reviews.sentiment_label.value_counts().to_dict(),
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
               'Review lengths are capped at 180 target words plus one filler sentence; this differs from long Yelp outliers. '
               'Source sentiment codes have no verified semantics and are not treated as labels. '
               'This report contains actual checks, not predictive accuracy or claims of business optimality.']
    (root/'reports'/'validation_report.md').write_text('\n'.join(report),encoding='utf-8')
    (root/'reports'/'validation_results.json').write_text(json.dumps({'checks':checks,'summary':summary,'comparisons':comparisons},indent=2),encoding='utf-8')
    return all(c[1] for c in checks)

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    config=yaml.safe_load((root/'config.yaml').read_text())
    p=json.loads((root/'reports'/'source_profile.json').read_text())
    sys.exit(0 if validate(root,load(root),config,p) else 1)
