"""Run locally with Python 3.11+: no network or paid services at runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import yaml
from src.audit import audit
from src.profile import profile
from src.generate_recipes import generate as recipes
from src.generate_trends import generate as trends
from src.generate_transactions import generate as transactions
from src.generate_social import generate as social,aggregate
from src.simulate_inventory import simulate
from src.generate_ml_datasets import generate as ml
from src.schema import emit,ORDER,sql_type
from src.validate import validate,load

ROOT=Path(__file__).resolve().parent

def pipeline(config,sales,stats):
    streams=[np.random.default_rng(s) for s in np.random.SeedSequence(config['seed']).spawn(4)]
    tables=recipes()
    print('Generating trends and latent demand...',flush=True)
    tables['market_trends']=trends(config,tables,streams[0])
    demand=transactions(config,tables,sales,streams[1])
    print(f'Simulating inventory for {len(demand):,} demand lines...',flush=True)
    tables.update(simulate(config,tables,demand,streams[2]))
    print('Generating synthetic Instagram menu discussion for Semarang...',flush=True)
    tables.update(social(config,tables,streams[3]))
    tables['menu_market_signals']=aggregate(tables)
    ml(config,tables)
    # Purge training/validation observations whose outcome windows overlap the next split.
    start=pd.Timestamp(config['start_date']); total=(pd.Timestamp(config['end_date'])-start).days+1
    boundaries={k:(start+pd.Timedelta(days=int(np.ceil(total*f)))).date().isoformat()
                for k,f in [('train',.7),('validation',.85)]}
    for name in ['restock_decision_dataset','inventory_risk_ml_dataset','trend_ml_dataset']:
        frame=tables[name]
        ends=frame.label_window_end.str[:10] if 'label_window_end' in frame else (pd.to_datetime(frame.decision_at.str[:10])+pd.Timedelta(days=7)).dt.strftime('%Y-%m-%d')
        for split,cutoff in boundaries.items():
            frame.loc[frame.split.eq(split)&ends.ge(cutoff),'split']='purged'
    return tables

def serialized(frame):
    data=frame.copy()
    for col in data:
        if sql_type(col,data[col]) in ('bigint','integer'):
            data[col]=data[col].astype('Int64')
    return data.to_csv(index=False,lineterminator='\n',float_format='%.6f',na_rep='').encode('utf-8')

def run():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,default=ROOT/'config.yaml')
    parser.add_argument('--audit-only',action='store_true')
    parser.add_argument('--verify-reproducibility',action='store_true')
    args=parser.parse_args()
    if sys.version_info<(3,11): raise RuntimeError('Python 3.11+ required')
    config=yaml.safe_load(args.config.read_text(encoding='utf-8'))
    if pd.Timestamp(config['end_date'])<pd.Timestamp(config['start_date']): raise ValueError('Invalid date range')
    if config['mean_daily_transactions_per_branch']<=0 or config['mean_daily_social_posts']<=0: raise ValueError('Invalid dataset size')
    if config['data_mode']!='synthetic' or config['social_platform']!='instagram': raise ValueError('This generator produces synthetic Instagram-like data only')
    if config['evaluation_horizon_days']!=7: raise ValueError('Current stockout target is defined for a seven-day horizon')
    for folder in ['output','reports','docs','sql']: (ROOT/folder).mkdir(exist_ok=True)
    frames,source_audit=audit(ROOT)
    for required in ['coffee-shop-sales-revenue.csv']:
        if required not in frames: raise FileNotFoundError(f'Missing essential source: {required}; see source_audit.md')
    sales,stats=profile(ROOT,frames)
    if args.audit_only:
        print('Audit/profile saved; no cafe-review sources are required.'); return
    tables=pipeline(config,sales,stats)
    hashes={}
    for name in ORDER:
        content=serialized(tables[name]); (ROOT/'output'/f'{name}.csv').write_bytes(content)
        hashes[name]=hashlib.sha256(content).hexdigest()
    emit(ROOT,tables)
    print('Validating exported CSV files...',flush=True)
    ok=validate(ROOT,load(ROOT),config,stats)
    manifest={'config':config,'source_sha256':{n:r.get('sha256') for n,r in source_audit.items()},
              'output_sha256':hashes,'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__}
    (ROOT/'reports'/'generation_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    if args.verify_reproducibility:
        print('Re-running clean in-memory generation with the same config and seed...',flush=True)
        repeated=pipeline(config,sales,stats)
        different=[name for name in ORDER if hashlib.sha256(serialized(repeated[name])).hexdigest()!=hashes[name]]
        (ROOT/'reports'/'reproducibility_report.md').write_text(
            '# Reproducibility\n\n' + f'{len(ORDER)-len(different)}/{len(ORDER)} CSV files byte-identical across two independent generations.\n\n'
            + 'Mismatches: '+str(different)+'\n\nFixed config, preserved input SHA-256, pinned dependencies, Python version and output hashes: generation_manifest.json.\n',encoding='utf-8')
        ok=ok and not different
    print('PASS' if ok else 'FAIL: inspect reports/validation_report.md',flush=True)
    if not ok: raise SystemExit(1)

if __name__=='__main__': run()
