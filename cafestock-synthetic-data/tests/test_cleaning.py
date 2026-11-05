import unittest
import pandas as pd
from src.cleaning import mark_sentiment_eligibility,text_fingerprint

class CleaningTests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame([
            (1,1,'2026-01-01T07:00:00+07:00','Matcha Enak','positive','train'),
            (2,2,'2026-08-01T07:00:00+07:00','  matcha   enak  ','positive','validation'),
            (3,3,'2026-10-01T07:00:00+07:00','MATCHA ENAK','negative','test'),
            (4,4,'2026-12-01T07:00:00+07:00','matcha enak','negative','pending')],
            columns=['post_id','mention_id','collected_at','content_text','sentiment_label','split'])

    def test_repeated_text_does_not_cross_eligible_partitions(self):
        data=mark_sentiment_eligibility(self.frame())
        self.assertEqual(data.training_status.tolist(),['eligible','duplicate','label_conflict','pending'])
        self.assertEqual(data.split.tolist(),['train','validation','test','pending'])

    def test_input_order_does_not_change_earliest_retention(self):
        data=mark_sentiment_eligibility(self.frame().iloc[::-1])
        self.assertEqual(data.set_index('post_id').loc[1,'training_status'],'eligible')

    def test_future_record_cannot_change_training_eligibility(self):
        first=mark_sentiment_eligibility(self.frame().iloc[:1])
        whole=mark_sentiment_eligibility(self.frame())
        self.assertEqual(first.loc[0,'training_status'],whole.loc[0,'training_status'])

    def test_unicode_and_whitespace_normalized_without_removing_negation(self):
        self.assertEqual(text_fingerprint('ＭＡＴＣＨＡ  enak'),text_fingerprint('matcha enak'))
        self.assertNotEqual(text_fingerprint('matcha enak'),text_fingerprint('matcha tidak enak'))

if __name__=='__main__': unittest.main()
