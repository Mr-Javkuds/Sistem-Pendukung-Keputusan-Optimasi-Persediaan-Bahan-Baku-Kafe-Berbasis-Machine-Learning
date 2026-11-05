"""Check train-only learning, negation, unseen values, and persisted transforms."""
from pathlib import Path
import tempfile
import unittest
import joblib
import numpy as np
import pandas as pd
from src.encoding import (fit_text,fit_tabular,transform_frame,fit_target,
                          transform_target,state_digest,matrix_digest)

class EncodingTests(unittest.TestCase):
    def config(self):
        return {'tfidf':{'ngram_range':[1,2],'min_df':1,'max_features':10000,
                         'sublinear_tf':True,'smooth_idf':True,'norm':'l2'}}

    def test_validation_tokens_do_not_enter_vocabulary(self):
        train=pd.DataFrame({'content_text':['matcha enak','matcha kurang enak']})
        model=fit_text(train,self.config()); before=state_digest(model,True)
        transform_frame(model,pd.DataFrame({'content_text':['tokenkhususvalidasi sekali']}),True)
        self.assertNotIn('tokenkhususvalidasi',model.vocabulary_)
        self.assertEqual(before,state_digest(model,True))

    def test_negation_retained_and_changes_representation(self):
        train=pd.DataFrame({'content_text':['matcha enak','matcha tidak enak']})
        model=fit_text(train,self.config())
        self.assertIn('tidak enak',model.vocabulary_)
        matrix=transform_frame(model,train,True)
        self.assertFalse(np.array_equal(matrix[0].toarray(),matrix[1].toarray()))

    def test_unknown_categories_and_missing_inference_do_not_refit(self):
        train=pd.DataFrame({'branch_id':[1,2,1],'consumption':[10.,20.,30.]})
        model=fit_tabular(train,['branch_id']); before=state_digest(model)
        heldout=pd.DataFrame({'branch_id':[999,np.nan],'consumption':[1000000.,np.nan]})
        matrix=transform_frame(model,heldout)
        self.assertTrue(np.isfinite(matrix.data).all())
        self.assertEqual(before,state_digest(model))
        self.assertNotIn(999,model.named_transformers_['categorical'].named_steps['onehot'].categories_[0])

    def test_numeric_imputer_uses_training_median(self):
        train=pd.DataFrame({'branch_id':[1,1,2],'consumption':[10.,np.nan,30.]})
        model=fit_tabular(train,['branch_id'])
        numeric=model.named_transformers_['numeric']
        self.assertEqual(numeric.named_steps['imputer'].statistics_[0],20.)
        self.assertEqual(numeric.named_steps['scaler'].mean_[0],20.)

    def test_serialized_text_transform_reproduces_matrix(self):
        train=pd.DataFrame({'content_text':['kopi enak','kopi pahit']})
        model=fit_text(train,self.config())
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'preprocessor.joblib'; joblib.dump(model,path)
            loaded=joblib.load(path)
            self.assertEqual(matrix_digest(transform_frame(model,train,True)),matrix_digest(transform_frame(loaded,train,True)))

    def test_unseen_target_label_is_rejected(self):
        encoder,_=fit_target('sentiment',pd.DataFrame({'sentiment_label':['positive','negative']}))
        with self.assertRaises(ValueError):
            transform_target('sentiment',pd.DataFrame({'sentiment_label':['new_class']}),encoder)

    def test_target_cannot_be_mistaken_for_text_input(self):
        with self.assertRaises(ValueError):
            fit_text(pd.DataFrame({'content_text':['enak'],'sentiment_label':['positive']}),self.config())

if __name__=='__main__': unittest.main()
