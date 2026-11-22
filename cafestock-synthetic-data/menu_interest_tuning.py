"""Validation-only candidate selection; confirmation is evaluated once afterward."""
from pathlib import Path
import gc
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for b in iter(lambda:stream.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def run(work,data,training,base):
    import pandas as pd
    import torch
    from laya import load
    from sklearn.metrics import accuracy_score,f1_score,classification_report,confusion_matrix
    assert torch.cuda.is_available(),'GPU required'
    source_manifest=json.loads((data.parent/'model_manifest.json').read_text(encoding='utf-8'))
    assert source_manifest['model_id']=='laya_menu_interest_v1'
    for name,digest in source_manifest['model_files_sha256'].items():assert sha(base/name)==digest,name
    labels=['positive','negative','neutral','mixed']
    validation=pd.read_csv(data/'validation.csv')
    instructions=(data/'instructions.txt').read_text(encoding='utf-8')
    frozen={str(p):sha(p) for p in [data/'validation.csv',data/'test.csv',training/'confirmation_locked.csv']}
    input_manifest=json.loads((training/'training_manifest.json').read_text())
    (work/'pretraining_lock.json').write_text(json.dumps({'sha256':frozen,'protocol':input_manifest},indent=2),encoding='utf-8')
    def predict(agent,questions,frame):
        result=[]
        texts=frame.content_text.tolist()
        for start in range(0,len(texts),64):
            outputs=agent.predict_batch([{'review':x} for x in texts[start:start+64]],questions,batch_size=8)
            result.extend(x['answers']['menu_interest']['choice'] for x in outputs)
        assert len(result)==len(frame) and set(result)<=set(labels)
        return result
    def metrics(frame,pred):
        y=frame.interest_label.tolist()
        return {'accuracy':float(accuracy_score(y,pred)),
            'macro_f1':float(f1_score(y,pred,labels=labels,average='macro',zero_division=0)),
            'classification_report':classification_report(y,pred,labels=labels,output_dict=True,zero_division=0),
            'confusion_matrix':confusion_matrix(y,pred,labels=labels).tolist(),'rows':len(y),'labels':labels}
    candidates=[{'name':'warm4','epochs':4,'encoder_lr':'1e-5','head_lr':'5e-5','smoothing':'.02'},
                {'name':'warm6','epochs':6,'encoder_lr':'1e-5','head_lr':'5e-5','smoothing':'.01'},
                {'name':'warm8','epochs':8,'encoder_lr':'1.5e-5','head_lr':'7.5e-5','smoothing':'.01'}]
    scores=[];candidate_root=work/'candidates';candidate_root.mkdir(exist_ok=True)
    for config in candidates:
        output=candidate_root/config['name']
        command=[sys.executable,'-m','laya.cli','train','--data',str(training/'train_augmented.csv'),
            '--eval',str(data/'validation.csv'),'--out',str(output),'--base',str(base),
            '--text-column','content_text','--label-column','interest_label','--question-id','menu_interest',
            '--instructions',instructions,'--epochs',str(config['epochs']),'--micro-batch','2','--grad-accum','8',
            '--encoder-lr',config['encoder_lr'],'--head-lr',config['head_lr'],'--loss','soft-ce',
            '--label-smoothing',config['smoothing'],'--shuffle-options','--max-len','256','--head-max-len','128',
            '--device','cuda','--seed','42']
        print('TRAIN CANDIDATE',config,flush=True)
        subprocess.run(command,check=True)
        agent=load(str(output),device='cuda');questions=json.loads((output/'questions.json').read_text(encoding='utf-8'))
        pred=predict(agent,questions,validation);evaluation=metrics(validation,pred)
        frame=validation.copy();frame['prediction']=pred;frame.to_csv(work/(config['name']+'_validation_predictions.csv'),index=False)
        entry={'config':config,'validation':evaluation,'checkpoint':str(output)};scores.append(entry)
        (work/'candidate_scores.json').write_text(json.dumps(scores,indent=2),encoding='utf-8')
        print('VALIDATION',config['name'],evaluation['accuracy'],evaluation['macro_f1'],flush=True)
        del agent;gc.collect();torch.cuda.empty_cache()
        if evaluation['accuracy']>.95 and evaluation['macro_f1']>.95:break
    selected=max(scores,key=lambda x:(min(x['validation']['accuracy'],x['validation']['macro_f1']),x['validation']['macro_f1']))
    model=work/'model'
    assert not model.exists(),'Refusing to replace an existing selected model'
    shutil.copytree(selected['checkpoint'],model,ignore=shutil.ignore_patterns('checkpoint_latest'))
    selection={'criterion':'validation only; max minimum(accuracy, macro F1)',
        'selected':selected['config'],'validation':selected['validation'],
        'validation_target_met':selected['validation']['accuracy']>.95 and selected['validation']['macro_f1']>.95,
        'confirmation_evaluations':0,'old_test_evaluations_after_selection':0}
    (work/'selection_frozen.json').write_text(json.dumps(selection,indent=2),encoding='utf-8')
    for path,digest in frozen.items():assert sha(Path(path))==digest
    # Neither holdout participates in any candidate decision above.
    agent=load(str(model),device='cuda');questions=json.loads((model/'questions.json').read_text(encoding='utf-8'))
    evaluations={}
    for name,path in [('legacy_test',data/'test.csv'),('confirmation',training/'confirmation_locked.csv')]:
        frame=pd.read_csv(path);pred=predict(agent,questions,frame);evaluation=metrics(frame,pred)
        frame['prediction']=pred;frame.to_csv(work/(name+'_predictions.csv'),index=False)
        frame[frame.prediction.ne(frame.interest_label)].to_csv(work/(name+'_errors.csv'),index=False)
        (work/(name+'_metrics.json')).write_text(json.dumps(evaluation,indent=2),encoding='utf-8')
        evaluations[name]=evaluation
        print(name,evaluation['accuracy'],evaluation['macro_f1'],flush=True)
    selection.update(confirmation_evaluations=1,old_test_evaluations_after_selection=1)
    (work/'selection_frozen.json').write_text(json.dumps(selection,indent=2),encoding='utf-8')
    manifest={'model_id':'laya_menu_interest_v2','task':'menu_interest','base_checkpoint':'laya_menu_interest_v1/model',
        'base_model_files_sha256':source_manifest['model_files_sha256'],
        'training':input_manifest,'selection':selection,'evaluations':evaluations,
        'confirmation_target_met':evaluations['confirmation']['accuracy']>.95 and evaluations['confirmation']['macro_f1']>.95,
        'provenance':'synthetic; no real-world accuracy claim',
        'model_files_sha256':{str(p.relative_to(model)):sha(p) for p in model.rglob('*') if p.is_file()}}
    (work/'model_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    # Only generated intermediate candidates under this job's working directory.
    assert candidate_root.resolve().is_relative_to(work.resolve()) and candidate_root.name=='candidates'
    shutil.rmtree(candidate_root)
    source=work/'source'
    if source.exists():
        assert source.resolve().is_relative_to(work.resolve()) and source.name=='source'
        shutil.rmtree(source)
    with zipfile.ZipFile(work.parent/'laya_menu_interest_v2.zip','w',zipfile.ZIP_STORED) as z:
        for p in work.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:z.write(p,p.relative_to(work.parent))
    print('TARGET REACHED ON CONFIRMATION:',manifest['confirmation_target_met'],flush=True)
