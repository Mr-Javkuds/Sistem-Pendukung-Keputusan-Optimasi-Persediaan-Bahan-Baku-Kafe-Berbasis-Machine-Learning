"""Kaggle runtime: train Laya interest, cap sources, run scenario RF ablations."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import zipfile

import numpy as np
import pandas as pd

LABELS = ['positive','negative','neutral','mixed']
SCORE = {'positive':1.,'negative':-1.,'neutral':0.,'mixed':0.}


def signals(comments, posts, label):
    """Cap first five collected comments, equal-weight sources; unknown tags excluded."""
    f=comments.merge(posts[['post_id','product_id','post_location_region_id']],on='post_id',suffixes=('','_post'))
    f=f[f.post_location_region_id.notna() & f[label].notna()].copy()
    f['score']=f[label].map(SCORE)
    assert f.score.notna().all()
    raw=f.groupby('post_id').size().rename('raw_comment_count')
    selected=f.sort_values(['comment_published_at','comment_id']).groupby('post_id',sort=False).head(5)
    per=selected.groupby(['post_id','product_id','post_location_region_id','collected_at'],as_index=False).agg(
        score=('score','mean'),selected_comments=('comment_id','size'))
    per=per.merge(raw,on='post_id')
    assert per.selected_comments.le(5).all()
    per['post_weight']=1.
    agg=per.groupby(['product_id','post_location_region_id','collected_at'],as_index=False).agg(
        score=('score','mean'),post_count=('post_id','size'),
        capped_comment_count=('selected_comments','sum'),raw_comment_count=('raw_comment_count','sum'))
    assert agg.capped_comment_count.le(5*agg.post_count).all()
    return agg,per


def available_menu_signal(frame, product, region, decision):
    known=frame[(frame.product_id.eq(product)) & frame.post_location_region_id.isin([1,region]) &
                (frame.collected_at < decision)]
    if known.empty:return 0.,0,0,0,None
    known=known[known.collected_at.eq(known.collected_at.max())]
    score=float(np.average(known.score,weights=known.post_count))
    at=known.collected_at.max()
    assert at<decision
    return score,int(known.post_count.sum()),int(known.capped_comment_count.sum()),int(known.raw_comment_count.sum()),at


def simulate_datasets(data, predicted, reference):
    """Three declared hypotheses; no real-world claim. Identical shocks across beta."""
    products=pd.read_csv(data/'products.csv');branches=pd.read_csv(data/'branches.csv')
    recipes=pd.read_csv(data/'recipes.csv');links=pd.read_csv(data/'recipe_ingredients.csv')
    links=links.merge(recipes[['recipe_id','product_id']],on='recipe_id')
    dates=pd.date_range('2026-03-24','2026-10-27',freq='7D',tz='Asia/Jakarta')+pd.Timedelta(hours=5)
    forecast_dates=[d for d in dates if d>=pd.Timestamp('2026-04-07',tz='Asia/Jakarta')]
    n=len(forecast_dates); cut1=int(.7*n);cut2=int(.85*n)
    partition={d.isoformat():('train' if i<cut1 else 'validation' if i<cut2 else 'test') for i,d in enumerate(forecast_dates)}
    rng=np.random.default_rng(20261108)
    shocks={};trend={};menu={}
    for k,d in enumerate(dates):
        for category in sorted(products.category_id.unique()):
            trend[(d.isoformat(),int(category))]=float(np.clip(50+23*np.sin(k/4+category)+rng.normal(0,6),0,100))
        for branch in branches.itertuples():
            for product in products.itertuples():
                key=(d.isoformat(),branch.branch_id,product.product_id)
                shocks[key]=float(rng.normal())
                menu[key]=(available_menu_signal(predicted,product.product_id,branch.region_id,d.isoformat()),
                           available_menu_signal(reference,product.product_id,branch.region_id,d.isoformat()))
    datasets={}
    for scenario,beta in [('strong',.8),('weak',.15),('none',0.)]:
        history={};rows=[]
        for k,d in enumerate(dates):
            requests={}
            for branch in branches.itertuples():
                for product in products.itertuples():
                    key=(d.isoformat(),branch.branch_id,product.product_id)
                    pred,gold=menu[key]
                    t=trend[(d.isoformat(),product.category_id)]
                    base=105*(1+.07*branch.branch_id)*(1+.03*product.product_id)
                    # Hypothesis uses reference labels; forecast features use predicted Laya labels.
                    mean=max(1.,base*(1+.25*(t-50)/50+beta*gold[0]))
                    requests[(branch.branch_id,product.product_id)]=max(0.,round(mean+np.sqrt(mean)*shocks[key]))
            for branch in branches.itertuples():
                for ingredient,g in links.groupby('ingredient_id'):
                    actual=sum(requests[(branch.branch_id,int(x.product_id))]*float(x.quantity) for x in g.itertuples())/7
                    key=(branch.branch_id,int(ingredient));past=history.get(key,[])
                    if d.isoformat() in partition:
                        quantities=np.array([float(x.quantity)*(1+.03*int(x.product_id)) for x in g.itertuples()])
                        entries=[menu[(d.isoformat(),branch.branch_id,int(x.product_id))][0] for x in g.itertuples()]
                        interest=float(np.average([v[0] for v in entries],weights=quantities))
                        market=float(np.average([trend[(d.isoformat(),int(products.set_index('product_id').loc[int(x.product_id),'category_id']))] for x in g.itertuples()],weights=quantities))
                        ats=[v[4] for v in entries if v[4]]
                        maximum=max(ats) if ats else None
                        assert not maximum or maximum<d.isoformat()
                        rows.append({'scenario':scenario,'branch_id':branch.branch_id,'ingredient_id':int(ingredient),
                            'decision_at':d.isoformat(),'target_end_exclusive':(d+pd.Timedelta(days=7)).isoformat(),
                            'split':partition[d.isoformat()],'mean_consumption_14d':float(np.mean(past[-2:])),
                            'week_of_year':d.isocalendar().week,'trend_index':market,'interest_score':interest,
                            'social_available':int(bool(ats)),'post_count':sum(v[1] for v in entries),
                            'capped_comments':sum(v[2] for v in entries),'raw_comments':sum(v[3] for v in entries),
                            'signal_max_available_at':maximum,
                            'target_daily_required':actual})
                    history.setdefault(key,[]).append(actual)
        f=pd.DataFrame(rows)
        assert f.decision_at.min()>'2026-04-01T00:00:00+07:00'
        # The last 7-day target in a partition ends at, not after, the next partition.
        for a,b in [('train','validation'),('validation','test')]:
            assert f.loc[f.split.eq(a),'target_end_exclusive'].max()<=f.loc[f.split.eq(b),'decision_at'].min()
        datasets[scenario]=f
    return datasets


def forecast_ablation(data,work,predicted,reference):
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.pipeline import Pipeline
    from sklearn.metrics import mean_absolute_error,mean_squared_error
    ingredients=pd.read_csv(data/'ingredients.csv').set_index('ingredient_id')
    datasets=simulate_datasets(data,predicted,reference)
    base=['branch_id','ingredient_id','mean_consumption_14d','week_of_year']
    social=['interest_score','social_available','post_count','capped_comments']
    groups={'A':base,'B':base+['trend_index'],'C':base+social,'D':base+['trend_index']+social}
    metrics=[]
    for scenario,frame in datasets.items():
        frame.to_csv(work/f'forecast_dataset_{scenario}.csv',index=False)
        train=frame[frame.split.eq('train')]
        for version,cols in groups.items():
            processor=ColumnTransformer([('ids',OneHotEncoder(handle_unknown='ignore'),['branch_id','ingredient_id'])],remainder='passthrough')
            model=Pipeline([('features',processor),('regressor',RandomForestRegressor(n_estimators=80,max_depth=12,min_samples_leaf=8,random_state=42,n_jobs=2))])
            model.fit(train[cols],train.target_daily_required)
            for part in ['validation','test']:
                f=frame[frame.split.eq(part)].copy();f['prediction']=model.predict(f[cols])
                f.to_csv(work/f'{scenario}_{version}_{part}_predictions.csv',index=False)
                for ingredient,g in f.groupby('ingredient_id'):
                    metrics.append({'scenario':scenario,'version':version,'split':part,'ingredient_id':int(ingredient),
                        'ingredient':ingredients.loc[ingredient,'ingredient_name'],'unit':ingredients.loc[ingredient,'unit'],
                        'rows':len(g),'mae':float(mean_absolute_error(g.target_daily_required,g.prediction)),
                        'rmse':float(np.sqrt(mean_squared_error(g.target_daily_required,g.prediction))),
                        'historical_mae':float(mean_absolute_error(g.target_daily_required,g.mean_consumption_14d))})
    result=pd.DataFrame(metrics);result.to_csv(work/'forecast_metrics_per_ingredient.csv',index=False)
    summaries={}
    for scenario,g in result[result.split.eq('test')].groupby('scenario'):
        pivot=g.pivot(index='ingredient_id',columns='version',values='mae')
        summaries[scenario]={v:{'mean_mae_ratio_to_A':float((pivot[v]/pivot.A).mean()),
            'ingredients_better_than_A':int(pivot[v].lt(pivot.A).sum())} for v in groups}
    (work/'ablation_summary.json').write_text(json.dumps(summaries,indent=2),encoding='utf-8')
    print('FORECAST ABLATION',json.dumps(summaries,indent=2),flush=True)
    return summaries


def run(work,data):
    import torch
    from laya import load
    from sklearn.metrics import accuracy_score,f1_score,classification_report,confusion_matrix
    assert torch.cuda.is_available(),'GPU Kaggle belum aktif'
    print('GPU',torch.cuda.get_device_name(0),flush=True)
    manifest=json.loads((data/'dataset_manifest.json').read_text())
    train=pd.read_csv(data/'train.csv');val=pd.read_csv(data/'validation.csv');test=pd.read_csv(data/'test.csv')
    for f in [train,val,test]:
        assert set(f.interest_label)==set(LABELS)
        assert not f.content_text.duplicated().any()
    assert train.collected_at.max()<val.collected_at.min()<test.collected_at.min()
    assert test.collected_at.max()<manifest['nlp_model_available_at']<manifest['forecast_start']
    for a,b in [(train,val),(train,test),(val,test)]:
        assert not(set(a.post_id)&set(b.post_id))
        assert not(set(a.family_id)&set(b.family_id))
        assert not(set(a.content_text)&set(b.content_text))
    model=work/'model';instructions=(data/'instructions.txt').read_text(encoding='utf-8')
    command=[sys.executable,'-m','laya.cli','train','--data',str(data/'train.csv'),'--eval',str(data/'validation.csv'),
        '--out',str(model),'--base','multilingual','--text-column','content_text','--label-column','interest_label',
        '--question-id','menu_interest','--instructions',instructions,'--epochs','2','--micro-batch','2','--grad-accum','8',
        '--encoder-lr','1e-5','--head-lr','5e-5','--loss','soft-ce','--label-smoothing','0.05','--shuffle-options',
        '--max-len','256','--head-max-len','128','--device','cuda','--seed','42']
    subprocess.run(command,check=True)
    agent=load(str(model),device='cuda');questions=json.loads((model/'questions.json').read_text(encoding='utf-8'))
    # Check tokenizer budget rather than silently truncating the new target definition.
    # The published model instructions are short; direct token check is independent of internal question adapters.
    head_tokens=len(agent.tok.encode('choice question: '+instructions,add_special_tokens=False))
    option_tokens=sum(1+len(agent.tok.encode(' '+label,add_special_tokens=False)) for label in LABELS)
    assert head_tokens+option_tokens<=128,(head_tokens,option_tokens)
    comments=pd.read_csv(data/'comments.csv');comments=comments[comments.split.ne('pending')].copy()
    texts=comments.content_text.drop_duplicates().tolist();cache={}
    for start in range(0,len(texts),64):
        chunk=texts[start:start+64]
        results=agent.predict_batch([{'review':t} for t in chunk],questions,batch_size=8)
        for t,r in zip(chunk,results):cache[t]=r['answers']['menu_interest']['choice']
        print('Interest inference',min(start+64,len(texts)),len(texts),flush=True)
    assert set(cache.values())<=set(LABELS)
    comments['interest_prediction']=comments.content_text.map(cache);assert comments.interest_prediction.notna().all()
    comments.to_csv(work/'comment_predictions.csv',index=False)
    test['prediction']=test.content_text.map(cache)
    metrics={'accuracy':float(accuracy_score(test.interest_label,test.prediction)),
        'macro_f1':float(f1_score(test.interest_label,test.prediction,labels=LABELS,average='macro',zero_division=0)),
        'classification_report':classification_report(test.interest_label,test.prediction,labels=LABELS,output_dict=True,zero_division=0),
        'confusion_matrix':confusion_matrix(test.interest_label,test.prediction,labels=LABELS).tolist(),
        'labels':LABELS,'rows':len(test),'provenance':'synthetic_interest_rule'}
    (work/'test_metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    test.to_csv(work/'nlp_test_predictions.csv',index=False)
    test[test.prediction.ne(test.interest_label)].to_csv(work/'nlp_test_errors.csv',index=False)
    cases=[('Rasanya enak.','neutral'),('Cuma menang tampilan, rasanya mengecewakan.','neutral'),
        ('Terlalu manis untuk seleraku.','neutral'),('Kelihatan enak, aku ingin coba!','positive'),
        ('Enak, tapi aku tidak tertarik mencoba.','negative'),('Pengin coba, tetapi masih ragu karena harganya.','mixed'),
        ('Toppingnya apa ya?','neutral'),('Aromanya menarik tapi terlalu manis.','neutral')]
    challenge=[]
    for text,expected in cases:
        state={'target_product':'Es Matcha Latte','parent_caption':'Menu ini diklaim enak dan viral. Apa ketertarikanmu?','comment_text':text}
        result=agent.predict({'review':json.dumps(state,ensure_ascii=False)},questions)
        challenge.append({'comment':text,'expected':expected,'prediction':result['answers']['menu_interest']['choice']})
    pd.DataFrame(challenge).to_csv(work/'policy_challenge.csv',index=False)
    posts=pd.read_csv(data/'posts.csv')
    predicted,per=signals(comments,posts,'interest_prediction');reference,_=signals(comments,posts,'interest_label')
    predicted.to_csv(work/'interest_signals_predicted.csv',index=False);per.to_csv(work/'post_weight_audit.csv',index=False)
    summary=forecast_ablation(data,work,predicted,reference)
    checks={'temporal_nlp_split':True,'post_group_disjoint':True,'phrase_family_disjoint':True,
        'checkpoint_before_forecast':True,'collection_before_decision':True,'post_comment_cap':5,
        'post_weight':1,'unknown_post_tags_excluded':True,'commenter_location_inferred':False,
        'forecast_target_windows_do_not_cross_partitions':True,'head_tokens':head_tokens,'option_tokens':option_tokens}
    (work/'audit.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    files={}
    for p in model.rglob('*'):
        if p.is_file() and 'checkpoint_latest' not in p.parts:
            h=hashlib.sha256()
            with p.open('rb') as stream:
                for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
            files[str(p.relative_to(model))]=h.hexdigest()
    (work/'model_manifest.json').write_text(json.dumps({'model_id':'laya_menu_interest_v1','task':'menu_interest',
        'dataset':manifest,'nlp_metrics':metrics,'ablation':summary,'checks':checks,'model_files_sha256':files},indent=2),encoding='utf-8')
    archive=work.parent/'laya_menu_interest_v1.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_STORED) as z:
        for p in work.rglob('*'):
            if p.is_file() and 'checkpoint_latest' not in p.parts:z.write(p,p.relative_to(work.parent))
    print('Saved new interest model:',archive,flush=True)
