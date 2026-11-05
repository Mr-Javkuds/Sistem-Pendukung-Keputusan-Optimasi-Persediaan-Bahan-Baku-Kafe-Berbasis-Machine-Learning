"""Execute evidence-producing preparation stages; no encoding or model training."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import pandas as pd
import yaml
from src.schema import ORDER,PRIMARY,FKS,sql_type
from src.cleaning import text_fingerprint

ROOT=Path(__file__).resolve().parent

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')

def write_csv(path,frame):
    path.parent.mkdir(parents=True,exist_ok=True)
    data=frame.copy()
    for col in data:
        if sql_type(col,data[col]) in ('bigint','integer'): data[col]=data[col].astype('Int64')
    path.write_text(data.to_csv(index=False,lineterminator='\n',float_format='%.6f'),encoding='utf-8',newline='')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--plot-python',default=sys.executable,help='Interpreter with optional matplotlib renderer installed')
    args=parser.parse_args()
    config=yaml.safe_load((ROOT/'config.yaml').read_text())
    manifest=json.loads((ROOT/'reports/generation_manifest.json').read_text())
    features=json.loads((ROOT/'docs/feature_manifest.json').read_text())
    tables={name:pd.read_csv(ROOT/'output'/f'{name}.csv') for name in ORDER}
    base=ROOT/'prepared'; rows=[]; checks=[]; warnings=[]
    dump(base/'source_generation_manifest.json',manifest)
    def check(stage,name,passed,detail=''):
        checks.append({'stage':stage,'check':name,'passed':bool(passed),'detail':str(detail)})
    for folder,hashes in [('input',manifest['source_sha256']),('output',manifest['output_sha256'])]:
        for key,expected in hashes.items():
            if expected is None: continue
            filename=key if folder=='input' else key+'.csv'
            path=ROOT/folder/filename
            actual=hashlib.sha256(path.read_bytes()).hexdigest()
            check(1,folder+'/'+filename+' hash',actual==expected)
            if folder=='output':
                frame=tables[key]
                rows.append({'table':key,'rows':len(frame),'columns':len(frame.columns),'sha256':actual,'provenance':'synthetic'})
    check(1,'Config matches generation manifest',manifest['config']==config)
    check(1,'Exactly the registered output tables exist',{p.stem for p in (ROOT/'output').glob('*.csv')}==set(ORDER))
    write_csv(base/'01_raw_dataset'/'table_inventory.csv',pd.DataFrame(rows))
    warnings.append('Source URLs/licenses are not fully documented; raw files and hashes exist, but source bibliography remains an academic limitation.')
    for name,frame in tables.items():
        check(2,name+' primary identity',frame[PRIMARY[name]].notna().all() and frame[PRIMARY[name]].is_unique)
        for col,parent in FKS.get(name,{}).items():
            check(2,name+' -> '+parent+' via '+col,frame[col].dropna().isin(tables[parent][PRIMARY[parent]]).all())
    s=tables['sentiment_ml_dataset']
    exact_duplicate_count=int(s.content_text.duplicated().sum())
    canonical=s.content_text.map(text_fingerprint)
    check(2,'Canonical audit matches stored fingerprints',canonical.eq(s.text_fingerprint).all())
    eligible=s[s.training_status=='eligible']
    check(2,'Eligible text fingerprints unique across all partitions',eligible.text_fingerprint.is_unique)
    check(2,'No pending or conflicting text is eligible',not eligible.split.eq('pending').any() and not s[s.training_status.isin(['duplicate','label_conflict','pending'])].index.isin(eligible.index).any())
    cleaning={'raw_posts':len(tables['social_posts']),'exact_duplicate_caption_occurrences':exact_duplicate_count,
              'canonical_duplicate_occurrences':int(canonical.duplicated().sum()),
              'original_text_groups_crossing_splits':int(s.groupby('text_fingerprint').split.nunique().gt(1).sum()),
              'training_status_counts':s.training_status.value_counts().to_dict(),
              'eligible_rows':len(eligible),'eligible_cross_split_text_groups':int(eligible.groupby('text_fingerprint').split.nunique().gt(1).sum()),
              'unknown_location_posts':int(tables['social_posts'].region_id.isna().sum()),
              'missing_cells_by_table':{n:{c:int(v) for c,v in t.isna().sum().items() if v} for n,t in tables.items()},
              'policy':'Raw posts and regional signal counts are retained as synthetic events. For text ML keep earliest collected canonical text only; exclude later duplicates/conflicts and pending batches. Unknown regions stay NULL and are excluded from regional aggregates. No fitting or imputation performed.'}
    dump(base/'02_data_cleaning'/'cleaning_summary.json',cleaning)
    warnings.append('Repeated synthetic captions are retained in market event tables; text-level ML excludes repeats. This is not an implemented Instagram spam detector.')
    risk=tables['inventory_risk_ml_dataset']; train=risk[risk.split=='train']
    train_s=eligible[eligible.split=='train']
    tx=tables['transactions'].set_index('transaction_id'); items=tables['transaction_items'].copy()
    items['at']=pd.to_datetime(items.transaction_id.map(tx.transaction_at),utc=True)
    # Include calendar training days, including sales after the final day's 05:00 decision.
    train_last_date=train.decision_at.str[:10].max()
    train_items=items[items.transaction_id.map(tx.transaction_at).str[:10]<=train_last_date]
    train_daily=train_items.groupby(train_items.transaction_id.map(tx.transaction_at).str[:10]).fulfilled_qty.sum()
    product_units=train_items.groupby('product_id').fulfilled_qty.sum().sort_values()
    product_names=tables['products'].set_index('product_id').product_name
    posts=tables['social_posts']; train_posts=posts[posts.collected_at.str[:10]<=train_last_date]
    summary={
        'scope':'Train-only outcome EDA; whole-dataset schema/duplicate checks are quality audits, not model selection.',
        'train_sentiment_labels':train_s.sentiment_label.value_counts().to_dict(),
        'train_risk_labels':{str(int(k)):int(v) for k,v in train.target_stockout.value_counts().items()},
        'train_product_units':{product_names.loc[k]:int(v) for k,v in product_units.items()},
        'train_daily_sales':{str(k):int(v) for k,v in train_daily.items()},
        'train_social_batches':{str(k):int(v) for k,v in train_posts.groupby(train_posts.collected_at.str[:7]).size().items()},
        'train_social_availability':{str(int(k)):int(v) for k,v in train.social_data_available.value_counts().items()},
        'train_risk_feature_description':train[features['risk_features']].describe().to_dict(),
        'train_unknown_location_posts':int(train_posts.region_id.isna().sum()),
        'train_daily_fulfilled_units_summary':train_daily.describe().to_dict()}
    summary_path=base/'03_eda'/'eda_summary.json'; dump(summary_path,summary)
    plot=subprocess.run([args.plot_python,str(ROOT/'src/plot_eda.py'),str(summary_path),str(ROOT/'reports/eda')],capture_output=True,text=True)
    check(3,'EDA overview chart rendered',plot.returncode==0,plot.stderr[-1000:] if plot.returncode else plot.stdout.strip())
    if plot.returncode: raise RuntimeError('Chart renderer failed; install requirements-eda.txt or select --plot-python. '+plot.stderr)
    check(3,'Train retains all four sentiment labels',set(train_s.sentiment_label)=={'positive','negative','neutral','mixed'})
    check(3,'Train retains both risk labels',set(train.target_stockout.dropna())=={0,1})
    eda_md=['# EDA tahap 03 — data sintetis, outcome train saja','',
            '![Train EDA](eda/eda_train_overview.png)','',
            f'Train sentiment eligible: {len(train_s):,} teks unik. Train risiko: {len(train):,} keputusan.',
            '', 'Temuan: kelas sentimen tidak seimbang; laporkan macro F1 dan metrik per kelas pada tahap evaluasi. '
            'Data sosial awal belum mempunyai batch yang selesai dikumpulkan, sehingga availability flag wajib dipakai. '
            'Template berulang dikeluarkan dari ML teks; evaluasi pada data ini tetap tidak membuktikan generalisasi Instagram nyata. '
            'Tren adalah pola yang diasumsikan simulator dan sentimen tidak dipaksakan sebagai penggerak permintaan.',
            '', 'Grafik unit menu, penjualan harian, distribusi target dan batch hanya mencakup train. '
            'Test tidak dipakai untuk memilih model, fitur, atau parameter. Grafik bersifat deskriptif, bukan hasil prediksi.']
    (ROOT/'reports/eda_report.md').write_text('\n'.join(eda_md),encoding='utf-8')
    tasks={
        'risk':('inventory_risk_ml_dataset',features['risk_features'],'target_stockout'),
        'restock_reference':('restock_decision_dataset',features['restock_features'],'baseline_purchase_qty'),
        'sentiment':('sentiment_ml_dataset',features['sentiment_features'],'sentiment_label'),
        'trend':('trend_ml_dataset',features['trend_features'],'target_fulfilled_units_next_7d')}
    contracts={}; split_summaries={}; artifact_rows=[]
    for task,(name,xcols,target) in tasks.items():
        frame=tables[name]
        check(4,task+' feature allowlist exists',set(xcols)<=set(frame.columns))
        check(4,task+' excludes its target and outcome metadata',target not in xcols and not set(xcols)&{'label_window_end','risk_label','label_observed','split','training_status','text_fingerprint'})
        check(4,task+' X is complete',frame[xcols].notna().all().all())
        if task!='sentiment': check(4,task+' numeric inputs finite',np.isfinite(frame[xcols].to_numpy(dtype=float)).all())
        if task=='sentiment': mask=frame.training_status.eq('eligible')
        elif task in ('risk','trend'): mask=frame.label_observed.eq(1)
        else: mask=pd.Series(True,index=frame.index)
        selected=frame[mask&frame.split.isin(['train','validation','test'])]
        contracts[task]={'source':name,'X':xcols,'y':target,'rows':len(selected),
            'rule':'training_status=eligible' if task=='sentiment' else ('label_observed=1' if task in ('risk','trend') else 'baseline reference policy; not a future-optimal quantity'),
            'fit_preprocessing':False,'model_trained':False}
        split_summaries[task]={}
        keys=set()
        for partition in ['train','validation','test']:
            part=selected[selected.split==partition].copy()
            identity='text_fingerprint' if task=='sentiment' else PRIMARY[name]
            current=set(part[identity])
            check(5,task+' '+partition+' nonempty',len(part)>0)
            check(5,task+' '+partition+' identities disjoint',not keys&current); keys|=current
            check(5,task+' '+partition+' targets observed',part[target].notna().all())
            meta=part.drop(columns=xcols+[target])
            for suffix,data in [('X',part[xcols]),('y',part[[target]]),('metadata',meta)]:
                path=base/'05_split_70_15_15'/task/(partition+'_'+suffix+'.csv')
                write_csv(path,data)
                actual=pd.read_csv(path)
                check(5,task+' '+partition+' '+suffix+' roundtrip rows/columns',len(actual)==len(part) and list(actual)==list(data))
                try:
                    pd.testing.assert_frame_equal(actual.reset_index(drop=True),data.reset_index(drop=True),check_dtype=False,atol=1e-6,rtol=1e-12)
                    values_match=True
                except AssertionError:
                    values_match=False
                check(5,task+' '+partition+' '+suffix+' roundtrip values/alignment',values_match)
                artifact_rows.append({'path':path.relative_to(ROOT).as_posix(),'rows':len(part),
                    'columns':list(data),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
            atcol='collected_at' if task=='sentiment' else 'decision_at'
            split_summaries[task][partition]={'rows':len(part),'first_at':str(part[atcol].min()),'last_at':str(part[atcol].max())}
        datecols=selected.collected_at if task=='sentiment' else selected.decision_at
        times={k:pd.to_datetime(datecols[selected.split==k],utc=True) for k in ['train','validation','test']}
        check(5,task+' chronological partitions',times['train'].max()<times['validation'].min() and times['validation'].max()<times['test'].min())
    dump(base/'04_feature_engineering'/'contracts.json',contracts)
    dump(base/'05_split_70_15_15'/'split_summary.json',split_summaries)
    dump(base/'artifact_manifest.json',artifact_rows)
    validation=json.loads((ROOT/'reports/validation_results.json').read_text())
    check(4,'Full independent relational/inventory/feature validation passed',all(c[1] for c in validation['checks']),f"{len(validation['checks'])} full checks")
    for col in ['social_available_at','social_feature_max_at','market_feature_max_at']:
        mask=risk[col].notna()
        check(4,col+' precedes decision',(pd.to_datetime(risk.loc[mask,col],utc=True)<pd.to_datetime(risk.loc[mask,'decision_at'],utc=True)).all())
    # Independently verify exact partition assignments rather than merely trusting labels.
    start=pd.Timestamp(config['start_date']); total=(pd.Timestamp(config['end_date'])-start).days+1
    boundaries={k:start+pd.Timedelta(days=int(np.ceil(total*f))) for k,f in [('train',.7),('validation',.85)]}
    for name in ['inventory_risk_ml_dataset','restock_decision_dataset','trend_ml_dataset']:
        frame=tables[name]; days=pd.to_datetime(frame.decision_at.str[:10])
        expected=pd.Series(np.where(days<boundaries['train'],'train',np.where(days<boundaries['validation'],'validation','test')),index=frame.index)
        ends=pd.to_datetime(frame.label_window_end.str[:10]) if 'label_window_end' in frame else days+pd.Timedelta(days=7)
        for group,cutoff in boundaries.items(): expected.loc[(expected==group)&(ends>=cutoff)]='purged'
        check(5,name+' exact calendar split/purge assignments',frame.split.eq(expected).all())
    report={'checks':checks,'warnings':warnings,'cleaning':cleaning,'splits':split_summaries,'source_and_output_hashes_verified':True,
            'model_training_performed':False,'prepared_artifact_count':len(artifact_rows)}
    dump(ROOT/'reports/steps_1_5_audit.json',report)
    lines=['# Audit tahap ML 01–05','',f"{sum(c['passed'] for c in checks)}/{len(checks)} pemeriksaan lulus.",'',
           '| Tahap | Status | Bukti |','|---|---|---|']
    for stage,name in [(1,'Raw dataset'),(2,'Data cleaning'),(3,'EDA'),(4,'Feature engineering'),(5,'Split 70/15/15')]:
        subset=[c for c in checks if c['stage']==stage]
        lines.append(f"| {stage:02d} {name} | {'PASS' if all(c['passed'] for c in subset) else 'FAIL'} | {sum(c['passed'] for c in subset)}/{len(subset)} checks |")
    lines+=['','## Perbaikan cleaning',
        f"Ditemukan {exact_duplicate_count:,} kemunculan caption identik berulang. Teks ML memakai training_status=eligible; "
        'kemunculan lebih baru dipertahankan sebagai catatan tetapi dikeluarkan dari modeling. Tidak ada teks identik '
        'yang eligible pada dua partisi. Caption mentah dan agregat event tidak ditulis ulang.',
        '', '## Baris siap modeling','| Tugas | Train | Validation | Test |','|---|---:|---:|---:|']
    for task,parts in split_summaries.items(): lines.append(f"| {task} | {parts['train']['rows']} | {parts['validation']['rows']} | {parts['test']['rows']} |")
    lines+=['','Nominal 70/15/15 berdasarkan kalender; proporsi baris berubah setelah deduplikasi, purge dan censoring. '
            'restock_reference masih target aturan baseline, bukan optimasi. Tidak ada encoding yang di-fit atau model dilatih.',
            '', '## Batas dan peringatan']+['- '+w for w in warnings]
    lines+=['','## Pemeriksaan gagal']+[c['check']+': '+c['detail'] for c in checks if not c['passed']]
    if all(c['passed'] for c in checks): lines.append('Tidak ada.')
    lines+=['','Rincian: steps_1_5_audit.json. EDA: eda_report.md. Prepared artifacts: ../prepared/artifact_manifest.json.']
    (ROOT/'reports/steps_1_5_audit.md').write_text('\n'.join(lines),encoding='utf-8')
    print(f"{sum(c['passed'] for c in checks)}/{len(checks)} preparation checks passed; {len(artifact_rows)} prepared CSV files exported")
    if not all(c['passed'] for c in checks): raise SystemExit(1)

if __name__=='__main__': main()
