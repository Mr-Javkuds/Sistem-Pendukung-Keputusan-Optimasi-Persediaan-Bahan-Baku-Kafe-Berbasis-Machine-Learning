"""One relationship registry drives CSV validation, DDL, import and documentation."""
import json
import pandas as pd

PRIMARY = {
 'regions':'region_id','social_posts':'post_id','menu_mentions':'mention_id',
 'menu_aspects':'menu_aspect_id','menu_market_signals':'signal_id',
 'branches':'branch_id','categories':'category_id','suppliers':'supplier_id','ingredients':'ingredient_id',
 'products':'product_id','recipes':'recipe_id','recipe_ingredients':'recipe_ingredient_id',
 'market_trends':'trend_id','latent_demand':'demand_id','transactions':'transaction_id',
 'transaction_items':'transaction_item_id',
 'purchase_orders':'purchase_order_id','purchase_order_items':'purchase_order_item_id',
 'inventory_movements':'movement_id','inventory_snapshots':'snapshot_id','stockout_events':'stockout_event_id',
 'waste_records':'waste_id','restock_decision_dataset':'decision_id',
 'inventory_risk_ml_dataset':'risk_row_id','sentiment_ml_dataset':'sentiment_row_id','trend_ml_dataset':'trend_row_id'}
FKS={
 'branches':{'region_id':'regions'},'social_posts':{'region_id':'regions'},
 'menu_mentions':{'post_id':'social_posts','product_id':'products'},
 'menu_aspects':{'mention_id':'menu_mentions'},
 'menu_market_signals':{'region_id':'regions','product_id':'products'},
 'ingredients':{'supplier_id':'suppliers'},'products':{'category_id':'categories'},
 'recipes':{'product_id':'products'},'recipe_ingredients':{'recipe_id':'recipes','ingredient_id':'ingredients'},
 'market_trends':{'category_id':'categories','region_id':'regions'},'latent_demand':{'branch_id':'branches','product_id':'products'},
 'transactions':{'branch_id':'branches'},
 'transaction_items':{'transaction_id':'transactions','demand_id':'latent_demand','product_id':'products'},
 'purchase_orders':{'branch_id':'branches','supplier_id':'suppliers'},
 'purchase_order_items':{'purchase_order_id':'purchase_orders','ingredient_id':'ingredients'},
 'inventory_movements':{'branch_id':'branches','ingredient_id':'ingredients','transaction_item_id':'transaction_items','purchase_order_item_id':'purchase_order_items'},
 'inventory_snapshots':{'branch_id':'branches','ingredient_id':'ingredients'},
 'stockout_events':{'transaction_item_id':'transaction_items','ingredient_id':'ingredients'},
 'waste_records':{'movement_id':'inventory_movements'},
 'restock_decision_dataset':{'branch_id':'branches','ingredient_id':'ingredients'},
 'inventory_risk_ml_dataset':{'branch_id':'branches','ingredient_id':'ingredients'},
 'sentiment_ml_dataset':{'mention_id':'menu_mentions','post_id':'social_posts','product_id':'products','region_id':'regions'},
 'trend_ml_dataset':{'category_id':'categories'}}
ORDER=['regions','branches','categories','suppliers','ingredients','products','recipes','recipe_ingredients',
       'market_trends','social_posts','menu_mentions','menu_aspects','menu_market_signals',
       'latent_demand','transactions','transaction_items',
       'purchase_orders','purchase_order_items','inventory_movements','inventory_snapshots','stockout_events',
       'waste_records','restock_decision_dataset','inventory_risk_ml_dataset','sentiment_ml_dataset','trend_ml_dataset']
NULLABLE={'transaction_item_id','purchase_order_item_id','delivered_at',
          'source_url','social_feature_max_at','social_available_at','social_period_start',
          'feature_max_at','future_stockout_7d','target_stockout','risk_label','target_fulfilled_units_next_7d'}
UNIQUE={'regions':[['region_name','city']],'branches':[['branch_name']],'categories':[['category_name']],
        'products':[['product_name']],'ingredients':[['ingredient_name']],
        'recipes':[['product_id']],'recipe_ingredients':[['recipe_id','ingredient_id']],
        'market_trends':[['category_id','week_start']], 'transaction_items':[['demand_id']],
        'social_posts':[['platform','source_post_key']], 'menu_mentions':[['post_id','product_id']],
        'menu_aspects':[['mention_id','aspect']],
        'menu_market_signals':[['region_id','product_id','period_start']],
        'inventory_snapshots':[['branch_id','ingredient_id','date']],
        'restock_decision_dataset':[['branch_id','ingredient_id','decision_at']]}

def sql_type(col,series):
    if col.endswith('_at') or col=='label_window_end': return 'timestamptz'
    if col in ('date','week_start','period_start','social_period_start'): return 'date'
    if col=='source_url': return 'text'
    if col.endswith('_id'): return 'bigint'
    if col in ('requested_qty','fulfilled_qty','lead_time_days','shelf_life_days','history_days',
               'social_post_count_latest_month','post_count','positive_count','neutral_count','negative_count',
               'mixed_count','social_data_available','social_age_days',
               'future_stockout_7d','target_stockout','label_observed','target_fulfilled_units_next_7d','unfulfilled_product_qty'): return 'integer'
    if pd.api.types.is_numeric_dtype(series): return 'numeric(20,6)'
    return 'text'

def is_nullable(name,col):
    if col=='region_id': return name in ('social_posts','sentiment_ml_dataset')
    return col in NULLABLE and (name=='inventory_movements' or col not in ('transaction_item_id','purchase_order_item_id'))

def emit(root,tables):
    ddl=['-- PostgreSQL 18; run in an empty dedicated database. No destructive DDL.', 'BEGIN;']
    imports=['\\set ON_ERROR_STOP on','-- Run from project root: psql -d cafestock -f sql/schema.sql -f sql/import.sql','BEGIN;']
    dictionary=['# Data dictionary','','All output rows are synthetic; input/ contains preserved external observations. '
                'Money is IDR; quantities use ingredients.unit (g, ml, piece); timestamps use Asia/Jakarta (+07:00). '
                'Empty CSV cells import as SQL NULL. IDs are stable application-assigned bigint keys.','']
    erd=['# Entity relationships','','```mermaid','erDiagram']
    for name in ORDER:
        frame=tables[name]; pk=PRIMARY[name]
        cols=[]
        dictionary += [f'## {name}', '', '| Field | PostgreSQL type | Meaning |','|---|---|---|']
        for col in frame:
            typ=sql_type(col,frame[col])
            nullable=col!=pk and is_nullable(name,col)
            constraint=' PRIMARY KEY' if col==pk else ('' if nullable else ' NOT NULL')
            if col in FKS.get(name,{}):
                parent=FKS[name][col]
                constraint+=f' REFERENCES {parent}({PRIMARY[parent]}) ON DELETE RESTRICT'
            cols.append(f'    {col} {typ}{constraint}')
            desc=describe(col)
            if col in FKS.get(name,{}): desc+=f'; FK to {FKS[name][col]}'
            if col==pk: desc+='; primary key'
            if nullable: desc+='; nullable'
            dictionary.append(f'| {col} | {typ} | {desc} |')
        for group in UNIQUE.get(name,[]): cols.append('    UNIQUE ('+', '.join(group)+')')
        for check in checks(name,frame): cols.append('    CHECK ('+check+')')
        ddl+=['CREATE TABLE '+name+' (',',\n'.join(cols),');']
        for col,parent in FKS.get(name,{}).items():
            covered=any(group[0]==col for group in UNIQUE.get(name,[]))
            covered=covered or (col=='branch_id' and name in ('transactions','inventory_movements'))
            if not covered:
                ddl.append(f'CREATE INDEX ON {name} ({col});')
            endpoint='o|' if is_nullable(name,col) else '||'
            child='o|' if name=='recipes' and col=='product_id' else 'o{'
            erd.append(f'    {parent} {endpoint}--{child} {name} : {col}')
        imports.append(f"\\copy {name} ({', '.join(frame.columns)}) FROM 'output/{name}.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8', NULL '')")
        dictionary.append('')
    ddl+=['CREATE INDEX ON transactions (branch_id, transaction_at);',
           'CREATE INDEX ON inventory_movements (branch_id, ingredient_id, movement_at);',
           'CREATE INDEX ON social_posts (region_id, collected_at);','COMMIT;']
    imports.append('COMMIT;')
    erd+=['```','','Every FK child has exactly one parent (1..1), except optional movement references and unknown social locations (0..1). '
          'Every parent permits 0..N children; recipes.product_id is UNIQUE, so a product permits 0..1 recipe '
          'in SQL and exactly one in this generated catalog, enforced by validation. '
          'Products and ingredients have a binary N:M relation through recipe_ingredients. '
          'Social posts have no purchase/transaction FK. Menu mentions connect external discussion to products; '
          'regions connect the market to branches. Unknown locations do not contribute to regional aggregates. '
          'No actual Instagram account, customer identity or real post URL is fabricated.','',
          'Operational entities are normalized to 3NF. ML tables deliberately duplicate decision-time '
          'supplier attributes and social text as immutable experiment snapshots. Recipe, conservation, '
          'FEFO, cross-table supplier consistency and temporal rules are enforced by the Python validator; '
          'they are not guaranteed by row CHECK constraints alone.','',
          'Indexes support FK joins, branch/time sales filters, ingredient movement reconstruction and '
          'social-data availability windows. Performance has not been benchmarked. No production migration is run. '
          'Rollback: discard the disposable database; this deletes its data and does not restore previous data.']
    (root/'sql'/'schema.sql').write_text('\n'.join(ddl)+'\n',encoding='utf-8')
    (root/'sql'/'import.sql').write_text('\n'.join(imports)+'\n',encoding='utf-8')
    (root/'docs'/'data_dictionary.md').write_text('\n'.join(dictionary),encoding='utf-8')
    (root/'docs'/'erd.md').write_text('\n'.join(erd),encoding='utf-8')
    excluded={'decision_id','risk_row_id','decision_at','market_feature_max_at','social_feature_max_at',
              'social_available_at','social_period_start',
              'label_window_end','future_stockout_7d','target_stockout','risk_label','label_observed','split'}
    manifest={'restock_features':[c for c in tables['restock_decision_dataset'] if c not in excluded],
              'restock_reference_target':'baseline_purchase_qty',
              'risk_features':[c for c in tables['inventory_risk_ml_dataset'] if c not in excluded and c!='baseline_purchase_qty'],
              'risk_target':'target_stockout', 'sentiment_features':['content_text'],
              'sentiment_target':'sentiment_label','trend_features':['category_id','interest_lag_1w'],
              'trend_target':'target_fulfilled_units_next_7d',
              'split_rule':'chronological 70/15/15; purge training label windows crossing next split boundary'}
    manifest['restock_features'].remove('baseline_purchase_qty')
    manifest['social_feature_contract']='Latest completed publication month collected before decision_at; mapped by city/district and recipe menu; unknown locations excluded.'
    manifest['sentiment_split_rule']='By collected_at; pending batches beyond simulation end excluded from training/evaluation.'
    manifest['sentiment_eligibility_rule']='Use training_status=eligible only. Canonical text deduplication retains earliest ingested occurrence; later duplicates/conflicts excluded without moving time partitions.'
    manifest['sentiment_excluded_metadata']=['text_fingerprint','training_status','split','sentiment_label','label_provenance','post_id','mention_id','region_id','product_id','published_at','collected_at','sentiment_row_id']
    manifest['sentiment_provenance']='synthetic Instagram-like Indonesian menu discussion; not real scraping or cafe reviews'
    (root/'docs'/'feature_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')

def checks(name,frame):
    result=[]
    for col in frame:
        if col in ('quantity','package_size','minimum_order_qty','shelf_life_days','lead_time_days') and name!='inventory_movements': result.append(f'{col} > 0')
        if col in ('on_hand','on_order','opening_stock','closing_stock','receipts','consumption','waste','requested_qty','fulfilled_qty','unit_price_idr','unit_cost_idr','base_price_idr','baseline_purchase_qty','shortage_qty','post_count','social_post_count_latest_month'): result.append(f'{col} >= 0')
    if name=='transaction_items': result.append('fulfilled_qty <= requested_qty')
    if name=='ingredients': result.append("unit IN ('g','ml','piece')")
    if name=='social_posts':
        result += ["platform = 'instagram'", "provenance = 'synthetic'",'collected_at >= published_at',
                   "(region_id IS NULL AND location_evidence = 'unknown') OR (region_id IS NOT NULL AND location_evidence = 'synthetic_scenario')"]
    if name=='menu_market_signals':
        result += ['post_count = positive_count + neutral_count + negative_count + mixed_count',
                   'sentiment_mean BETWEEN -1 AND 1','available_at >= source_max_published_at']
    if 'menu_sentiment_latest_month' in frame: result.append('menu_sentiment_latest_month BETWEEN -1 AND 1')
    if 'sentiment_label' in frame: result.append("sentiment_label IN ('positive','neutral','negative','mixed')")
    if name=='sentiment_ml_dataset': result += ["training_status IN ('eligible','duplicate','label_conflict','pending')",'length(text_fingerprint) = 64']
    if name=='market_trends': result.append('interest_index BETWEEN 0 AND 100')
    if name=='inventory_snapshots': result.append('abs(closing_stock - (opening_stock + receipts - consumption - waste + adjustments)) < 0.00001')
    if name=='purchase_orders':
        result += ["status IN ('open','delivered')",'expected_delivery_at > ordered_at',
                   "(status = 'open' AND delivered_at IS NULL) OR (status = 'delivered' AND delivered_at IS NOT NULL)"]
    return result

def describe(col):
    meanings={
        'quantity':'Ingredient base units; signed delta only in inventory_movements',
        'requested_qty':'Simulated latent product units requested',
        'fulfilled_qty':'Product units actually fulfilled and consuming recipe ingredients',
        'source_product_type_proxy':'Explicit source type used for statistical sampling; not source identity',
        'history_days':'Number of completed days used, capped at 14; zero uses engineering prior',
        'mean_daily_consumption_14d':'Prior completed-day mean ingredient consumption in base units/day',
        'on_hand':'Usable base units at 05:00 after expiry, adjustments and receipts',
        'on_order':'Outstanding units before this decision order',
        'baseline_purchase_qty':'Reference policy quantity in base units; not mathematically optimal',
        'future_stockout_7d':'Evaluation target: shortage event in configured horizon; NULL if censored',
        'target_stockout':'Same evaluation outcome as restock table; excluded from features',
        'label_observed':'1 if complete future outcome window is available, otherwise 0',
        'market_feature_max_at':'Latest source timestamp of historical synthetic weekly interest feature',
        'content_text':'Original synthetic Indonesian discussion about a menu, not a cafe review',
        'text_fingerprint':'SHA-256 of NFKC/casefold/whitespace-normalized text, used for audit/dedup only; excluded from model inputs',
        'training_status':'Use eligible only for modeling; later duplicate, label_conflict and pending records remain auditable but excluded',
        'collected_at':'Simulated monthly ingestion time; later than publication; gates feature availability',
        'source_url':'NULL for synthetic content; no real Instagram link is claimed',
        'location_evidence':'synthetic_scenario for assigned market or unknown; never inferred from account location',
        'source_location_proxy':'Explicit unrelated source location used only to transfer transaction patterns',
        'social_feature_max_at':'Latest publication time used in the historical menu sentiment feature',
        'social_available_at':'Latest actual synthetic monthly collection time contributing to features',
        'social_period_start':'Publication month represented in latest available regional menu signals',
        'social_post_count_latest_month':'Count of available menu discussions for linked products in city plus branch district',
        'menu_sentiment_latest_month':'Mean menu opinion: positive=1, negative=-1, neutral/mixed=0; missing flagged separately',
        'social_data_available':'0 means no eligible collected batch; score 0 must not be interpreted as observed neutrality',
        'social_age_days':'Days since contributing monthly batch availability; 0 with availability flag 0 means missing',
        'market_interest_latest':'Equal mean of latest known category indices associated via recipes',
        'unit_cost_idr':'IDR per ingredient base unit; invented local cost, not an FX conversion',
        'package_size':'Purchase-package quantity in ingredient base units',
        'minimum_order_qty':'Minimum purchase units, a package multiple',
        'shortage_qty':'Ingredient units short before fulfilling the requested product',
        'split':'Chronological train/validation/test; boundary label rows are purged from training',
    }
    return meanings.get(col,col.replace('_',' ').capitalize())
