"""Stage 06: fit train-only preprocessing, encode fixed time splits, and validate."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import joblib
import numpy as np
import pandas as pd
from scipy import sparse
import scipy
import sklearn
import yaml
from src.encoding import (fit_text,fit_tabular,transform_frame,fit_target,transform_target,
                          fitted_state,state_digest,matrix_digest)
from src.schema import PRIMARY

ROOT=Path(__file__).resolve().parent
PARTITIONS=['train','validation','test']

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')

def verify_upstream(root):
    """Fail before fitting if prepared files or their generation have changed."""
    generation=json.loads((root/'reports/generation_manifest.json').read_text())
    binding=json.loads((root/'prepared/source_generation_manifest.json').read_text())
    if generation!=binding: raise ValueError('Prepared data is bound to a different generation; rerun audit_steps_1_5.py')
    for folder,hashes in [('output',generation['output_sha256']),('input',generation['source_sha256'])]:
        for name,expected in hashes.items():
            if expected is None: continue
            filename=name+'.csv' if folder=='output' else name
            if sha(root/folder/filename)!=expected: raise ValueError('Upstream data changed: '+folder+'/'+filename)
    artifacts=json.loads((root/'prepared/artifact_manifest.json').read_text())
    for artifact in artifacts:
        if sha(root/artifact['path'])!=artifact['sha256']: raise ValueError('Prepared artifact changed: '+artifact['path'])
    audit=json.loads((root/'reports/steps_1_5_audit.json').read_text())
    if not all(row['passed'] for row in audit['checks']): raise ValueError('Stages 1–5 have failing checks')
    return generation,artifacts

def same_frame(left,right):
    try:
        pd.testing.assert_frame_equal(left.reset_index(drop=True),right.reset_index(drop=True),check_dtype=False,atol=1e-6,rtol=1e-12)
        return True
    except AssertionError: return False

def run():
    parser=argparse.ArgumentParser()
    parser.add_argument('--verify-reproducibility',action='store_true')
    args=parser.parse_args()
    if sys.version_info<(3,11): raise RuntimeError('Python 3.11+ required')
    generation,input_artifacts=verify_upstream(ROOT)
    config=yaml.safe_load((ROOT/'encoding_config.yaml').read_text())
    contracts=json.loads((ROOT/'prepared/04_feature_engineering/contracts.json').read_text())
    supported={'numeric_imputation':'median','numeric_scaling':'standard',
               'categorical_unknown':'ignore','text_normalization':'NFKC_casefold_whitespace'}
    if any(config.get(k)!=v for k,v in supported.items()):
        raise ValueError('Unsupported preprocessing policy; update the implementation and tests rather than silently ignoring config')
    if set(config['categorical_features'])!=set(contracts)-{'sentiment'}:
        raise ValueError('Categorical feature contracts do not match tasks')
    destination=ROOT/'prepared/06_encoding'; destination.mkdir(exist_ok=True)
    checks=[]; results={}; outputs=[]
    def check(name,passed,detail=''):
        checks.append({'check':name,'passed':bool(passed),'detail':str(detail)})
        if not passed: print('FAIL:',name,detail,flush=True)
    for task,contract in contracts.items():
        print('Encoding',task,'from train only...',flush=True)
        split_dir=ROOT/'prepared/05_split_70_15_15'/task
        data={p:{kind:pd.read_csv(split_dir/(p+'_'+kind+'.csv')) for kind in ['X','y','metadata']} for p in PARTITIONS}
        original=pd.read_csv(ROOT/'output'/(contract['source']+'.csv')).set_index(PRIMARY[contract['source']],drop=False)
        identity=PRIMARY[contract['source']]
        for partition,parts in data.items():
            X,y,metadata=parts['X'],parts['y'],parts['metadata']
            check(task+' '+partition+' exact input contract',list(X)==contract['X'] and list(y)==[contract['y']])
            check(task+' '+partition+' row alignment',len(X)==len(y)==len(metadata))
            source=original.loc[metadata[identity]].reset_index(drop=True)
            check(task+' '+partition+' X agrees with source identities',same_frame(X,source[contract['X']]))
            check(task+' '+partition+' y agrees with source identities',same_frame(y,source[[contract['y']]]))
            check(task+' '+partition+' metadata agrees with source identities',same_frame(metadata,source[list(metadata)]))
            check(task+' '+partition+' only correct time split',metadata.split.eq(partition).all())
            if task=='sentiment': check(task+' '+partition+' eligible text only',metadata.training_status.eq('eligible').all())
            if task in ('risk','trend'): check(task+' '+partition+' observed target only',metadata.label_observed.eq(1).all())
        if not all(c['passed'] for c in checks): raise RuntimeError('Invalid inputs; no fitting performed for '+task)
        text=task=='sentiment'; train=data['train']
        transformer=fit_text(train['X'],config) if text else fit_tabular(train['X'],config['categorical_features'][task])
        encoder,label_mapping=fit_target(task,train['y'])
        learned=fitted_state(transformer,text); before=state_digest(transformer,text)
        names=transformer.get_feature_names_out().tolist()
        check(task+' output feature names unique',len(names)==len(set(names)))
        if text:
            analyzer=transformer.build_analyzer()
            document_frequency=Counter()
            for content in train['X'].content_text: document_frequency.update(set(analyzer(content)))
            expected=np.array([np.log((1+len(train['X']))/(1+document_frequency[name]))+1 for name in names])
            check('TF-IDF vocabulary comes from train',set(names)<=set(document_frequency))
            check('TF-IDF IDF independently matches train document frequencies',np.allclose(transformer.idf_,expected,atol=2e-6,rtol=1e-6))
            check('TF-IDF respects train min_df',all(document_frequency[n]>=config['tfidf']['min_df'] for n in names))
        else:
            for column,categories in learned['categories'].items():
                check(task+' '+column+' categories learned from train',set(categories)==set(train['X'][column].dropna().tolist()))
            numeric=train['X'][learned['numeric_features']].to_numpy(dtype=float)
            medians=np.nanmedian(numeric,axis=0)
            check(task+' medians learned from train',np.allclose(learned['numeric_imputation_statistics'],medians))
            filled=np.where(np.isnan(numeric),medians,numeric)
            check(task+' scaler mean learned from train',np.allclose(learned['numeric_mean'],filled.mean(axis=0)))
            check(task+' scaler variance learned from train',np.allclose(learned['numeric_variance'],filled.var(axis=0)))
            check(task+' scaler sample count is train only',learned['numeric_samples_seen']==len(train['X']))
        target_dir=destination/task; target_dir.mkdir(exist_ok=True)
        joblib.dump(transformer,target_dir/'preprocessor.joblib',compress=3)
        if encoder is not None: joblib.dump(encoder,target_dir/'target_encoder.joblib',compress=3)
        dump(target_dir/'feature_names.json',names)
        dump(target_dir/'fitted_state.json',learned)
        dump(target_dir/'label_mapping.json',label_mapping or {'target':contract['y'],'encoding':'unchanged numeric target'})
        matrices={}; partitions={}
        for partition,parts in data.items():
            matrix=transform_frame(transformer,parts['X'],text); matrices[partition]=matrix
            target=transform_target(task,parts['y'],encoder)
            sparse.save_npz(target_dir/(partition+'_X.npz'),matrix,compressed=True)
            np.save(target_dir/(partition+'_y.npy'),target,allow_pickle=False)
            # Copy exact source metadata bytes; row order is already audited.
            (target_dir/(partition+'_metadata.csv')).write_bytes((split_dir/(partition+'_metadata.csv')).read_bytes())
            restored=sparse.load_npz(target_dir/(partition+'_X.npz'))
            check(task+' '+partition+' matrix/target shape',matrix.shape==(len(parts['X']),len(names)) and len(target)==len(parts['y']))
            check(task+' '+partition+' finite matrix',np.isfinite(matrix.data).all())
            check(task+' '+partition+' sparse roundtrip identical',matrix_digest(matrix)==matrix_digest(restored))
            check(task+' '+partition+' target roundtrip identical',np.array_equal(target,np.load(target_dir/(partition+'_y.npy'),allow_pickle=False)))
            if text:
                check('TF-IDF '+partition+' nonnegative',bool((matrix.data>=0).all()))
                check('Sentiment '+partition+' reversible labels',np.array_equal(encoder.inverse_transform(target),parts['y'].iloc[:,0].to_numpy()))
                zero_rows=int((np.diff(matrix.indptr)==0).sum())
                tokens=[token for value in parts['X'].content_text for token in analyzer(value)]
                unseen=sum(token not in transformer.vocabulary_ for token in tokens)
                detail={'zero_vector_rows':zero_rows,'out_of_vocabulary_ngram_occurrences':int(unseen),'analyzed_ngram_occurrences':len(tokens)}
            else:
                detail={'unknown_categories':{column:int((~parts['X'][column].isin(categories)&parts['X'][column].notna()).sum()) for column,categories in learned['categories'].items()}}
                if task=='risk': check('Risk '+partition+' binary targets unchanged',np.array_equal(target,parts['y'].iloc[:,0].to_numpy()))
                if task=='restock_reference': check('Restock '+partition+' reference quantity unchanged',np.allclose(target,parts['y'].iloc[:,0]))
                if task=='trend': check('Trend '+partition+' units unchanged',np.array_equal(target,parts['y'].iloc[:,0].to_numpy()))
            partitions[partition]={'rows':matrix.shape[0],'features':matrix.shape[1],'nonzero':int(matrix.nnz),
                'matrix_numerical_sha256':matrix_digest(matrix),'target_shape':list(target.shape),**detail}
        check(task+' validation/test transforms do not change fitted state',before==state_digest(transformer,text))
        loaded=joblib.load(target_dir/'preprocessor.joblib')
        check(task+' serialized transformer preserves state',state_digest(loaded,text)==before)
        check(task+' serialized transformer reproduces test matrix',matrix_digest(transform_frame(loaded,data['test']['X'],text))==matrix_digest(matrices['test']))
        if args.verify_reproducibility:
            repeated=fit_text(train['X'],config) if text else fit_tabular(train['X'],config['categorical_features'][task])
            check(task+' independently refitted train state identical',state_digest(repeated,text)==before)
            for partition,parts in data.items():
                check(task+' '+partition+' independent encoding identical',matrix_digest(transform_frame(repeated,parts['X'],text))==matrix_digest(matrices[partition]))
        results[task]={'input_features':contract['X'],'encoded_features':len(names),'target':contract['y'],
            'fit_partition':'train','fit_rows':len(train['X']),'preprocessor_state_sha256':before,
            'label_mapping':label_mapping,'partitions':partitions,'prediction_model_trained':False,
            'reference_only':task=='restock_reference'}
        for path in sorted(target_dir.iterdir()):
            if path.is_file(): outputs.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size})
    report={'stage':'06_encoding','checks':checks,'tasks':results,'config':config,
        'prediction_models_trained':False,'preprocessing_fit_partition':'train',
        'reproducibility_checked':args.verify_reproducibility,
        'versions':{'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'scikit_learn':sklearn.__version__,'joblib':joblib.__version__},
        'source_generation_manifest_sha256':sha(ROOT/'reports/generation_manifest.json'),
        'prepared_artifact_manifest_sha256':sha(ROOT/'prepared/artifact_manifest.json'),
        'code_and_contract_sha256':{name:sha(ROOT/name) for name in ['encode.py','src/encoding.py','encoding_config.yaml','prepared/04_feature_engineering/contracts.json','docs/feature_manifest.json']},
        'input_artifacts':input_artifacts,'output_artifacts':outputs}
    dump(destination/'manifest.json',report)
    dump(ROOT/'reports/encoding_report.json',report)
    lines=['# Tahap 06 — Encoding','',f"{sum(c['passed'] for c in checks)}/{len(checks)} checks passed.",'',
        'Preprocessing dipelajari dari train saja. Tidak ada classifier/regressor yang dilatih atau skor prediksi yang dihitung.',
        '', '| Tugas | Train | Validation | Test | Dimensi X |','|---|---:|---:|---:|---:|']
    for task,row in results.items(): lines.append(f"| {task} | {row['partitions']['train']['rows']} | {row['partitions']['validation']['rows']} | {row['partitions']['test']['rows']} | {row['encoded_features']} |")
    lines+=['', 'Teks: normalisasi NFKC/casefold/whitespace, unigram–bigram TF-IDF, min_df=2, '
        'max_features=10000, sublinear TF, smooth IDF, L2 norm, tanpa penghapusan stopword/negasi. '
        'Kosakata dan IDF hanya dari train. LabelEncoder sentimen hanya dipelajari dari label train.',
        '', 'Tabular: branch_id/ingredient_id/category_id diperlakukan nominal dengan one-hot. '
        'Kategori baru diabaikan oleh encoder dan harus ditandai sebagai masalah cakupan saat serving. '
        'Numerik diimputasi median train, lalu StandardScaler train untuk kompatibilitas pembanding linear; '
        'Random Forest tidak mensyaratkan scaling. Missing indicator hanya muncul jika ada missing saat fit. '
        'Data aktual saat ini lengkap; perilaku missing/unknown diuji terpisah.',
        '', 'ID baris, split, fingerprint, waktu label, target, dan metadata lain tidak masuk X. '
        'Risk tetap binary; target regresi tetap satuan aslinya. restock_reference masih meniru aturan '
        'baseline dan bukan target pembelian optimal.',
        '', '## Batas penggunaan',
        'Artefak ini untuk split tetap yang sudah disiapkan. Pada cross-validation/tuning berikutnya, '
        'preprocessing harus di-fit ulang di setiap fold training melalui Pipeline, bukan memakai encoder '
        'yang sudah melihat semua train untuk mengevaluasi fold awal. TF-IDF dan encoder yang disimpan '
        'boleh digunakan untuk prediksi data baru dengan kontrak kolom yang sama.',
        '', 'Data tetap sintetis. Fitur sentimen risiko adalah label aturan referensi, belum prediksi SVM '
        'out-of-fold. Memakai sentiment_mean referensi tidak membuktikan alur NLP end-to-end. '
        'Transformer joblib hanya boleh dimuat dari artefak proyek yang dipercaya; hash sumber/output '
        'tersedia di manifest. Reproduksibilitas diverifikasi pada state dan nilai matriks, '
        'bukan menjanjikan byte identik untuk semua format biner lintas versi.',
        '', '## Pemeriksaan gagal']
    failures=[c for c in checks if not c['passed']]
    lines+=['- '+c['check']+': '+c['detail'] for c in failures] if failures else ['Tidak ada.']
    lines+=['','Rincian pemeriksaan, versi, OOV, hash dan state: encoding_report.json. '
        'Artefak: ../prepared/06_encoding/. Langkah berikutnya: 07_modeling.']
    (ROOT/'reports/encoding_report.md').write_text('\n'.join(lines),encoding='utf-8')
    print(f"{sum(c['passed'] for c in checks)}/{len(checks)} encoding checks passed",flush=True)
    if failures: raise SystemExit(1)

if __name__=='__main__': run()
