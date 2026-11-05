"""Train-only preprocessing; no prediction model or feature selection is fitted."""
import hashlib
import json
import re
import unicodedata
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder,StandardScaler,LabelEncoder

def normalize_text(value):
    return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',str(value)).casefold()).strip()

def fit_text(train_frame,config):
    if list(train_frame.columns)!=['content_text']: raise ValueError('Text input must contain content_text only')
    options=dict(config['tfidf']); options['ngram_range']=tuple(options['ngram_range'])
    transformer=TfidfVectorizer(preprocessor=normalize_text,lowercase=False,stop_words=None,
        dtype=np.float32,**options)
    transformer.fit(train_frame.content_text.tolist())
    return transformer

def fit_tabular(train_frame,categorical_columns):
    if not set(categorical_columns)<=set(train_frame): raise ValueError('Missing categorical features')
    numeric_columns=[c for c in train_frame if c not in categorical_columns]
    if not len(train_frame): raise ValueError('Empty train split')
    if np.isinf(train_frame.to_numpy(dtype=float)).any(): raise ValueError('Infinite training values')
    categorical=Pipeline([
        ('imputer',SimpleImputer(strategy='constant',fill_value=-1,keep_empty_features=True)),
        ('onehot',OneHotEncoder(handle_unknown='ignore',sparse_output=True,dtype=np.float32))])
    numeric=Pipeline([
        ('imputer',SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True)),
        ('scaler',StandardScaler())])
    transformer=ColumnTransformer([
        ('categorical',categorical,categorical_columns),
        ('numeric',numeric,numeric_columns)],remainder='drop',sparse_threshold=1.0,verbose_feature_names_out=True)
    transformer.fit(train_frame)
    return transformer

def transform_frame(transformer,frame,text=False):
    values=transformer.transform(frame.content_text.tolist()) if text else transformer.transform(frame)
    matrix=sparse.csr_matrix(values,dtype=np.float32)
    matrix.sort_indices(); matrix.eliminate_zeros()
    if not np.isfinite(matrix.data).all(): raise ValueError('Encoded matrix contains nonfinite values')
    return matrix

def fit_target(task,train_y):
    target=train_y.iloc[:,0]
    if task=='sentiment':
        encoder=LabelEncoder().fit(target)
        return encoder,{str(label):int(i) for i,label in enumerate(encoder.classes_)}
    if task=='risk':
        if set(target)!={0,1}: raise ValueError('Risk train must include both binary labels')
        return None,{'no_stockout':0,'stockout':1}
    return None,None

def transform_target(task,frame,encoder):
    values=frame.iloc[:,0]
    if values.isna().any(): raise ValueError('Missing target')
    if task=='sentiment': return encoder.transform(values).astype(np.int8)
    if task=='risk':
        if not set(values)<={0,1}: raise ValueError('Invalid binary risk label')
        return values.to_numpy(dtype=np.int8)
    if task=='trend': return values.to_numpy(dtype=np.int64)
    return values.to_numpy(dtype=np.float64)

def matrix_digest(matrix):
    matrix=sparse.csr_matrix(matrix,dtype=np.float32).copy(); matrix.sort_indices(); matrix.eliminate_zeros()
    digest=hashlib.sha256()
    for array in [np.asarray(matrix.shape,dtype='<i8'),matrix.indptr.astype('<i8'),
                  matrix.indices.astype('<i8'),matrix.data.astype('<f4')]:
        digest.update(array.tobytes())
    return digest.hexdigest()

def fitted_state(transformer,text=False):
    if text:
        return {'feature_names':transformer.get_feature_names_out().tolist(),
                'idf':transformer.idf_.astype(float).tolist(),
                'normalization':'NFKC/casefold/whitespace; negation retained; no stopword removal'}
    categorical=transformer.named_transformers_['categorical']
    numeric=transformer.named_transformers_['numeric']
    return {'feature_names':transformer.get_feature_names_out().tolist(),
            'categorical_features':list(transformer.transformers_[0][2]),
            'categories':{name:values.tolist() for name,values in zip(transformer.transformers_[0][2],categorical.named_steps['onehot'].categories_)},
            'numeric_features':list(transformer.transformers_[1][2]),
            'numeric_imputation_statistics':numeric.named_steps['imputer'].statistics_.tolist(),
            'missing_indicators':numeric.named_steps['imputer'].indicator_.features_.tolist(),
            'numeric_mean':numeric.named_steps['scaler'].mean_.tolist(),
            'numeric_variance':numeric.named_steps['scaler'].var_.tolist(),
            'numeric_scale':numeric.named_steps['scaler'].scale_.tolist(),
            'numeric_samples_seen':int(numeric.named_steps['scaler'].n_samples_seen_)}

def state_digest(transformer,text=False):
    return hashlib.sha256(json.dumps(fitted_state(transformer,text),sort_keys=True,ensure_ascii=False,allow_nan=False).encode('utf-8')).hexdigest()
