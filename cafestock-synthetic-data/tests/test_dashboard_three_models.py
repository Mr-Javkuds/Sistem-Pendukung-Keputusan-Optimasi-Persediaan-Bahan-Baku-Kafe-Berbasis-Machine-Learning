"""HTTP dispatch and actual input adapters, without loading heavyweight weights."""
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import owner_app


class Agent:
    def __init__(self, question, label):
        self.question=question;self.label=label;self.calls=[];self.probability=.8

    def predict(self, state, questions):
        self.calls.append((state,questions))
        return {'answers':{self.question:{'choice':self.label,'probabilities':{self.label:self.probability}}}}


class ThreeModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        cls.product=cls.root/'product';cls.trend=cls.root/'trend'
        for folder,question in [(cls.product,'sentiment'),(cls.trend,'menu_interest')]:
            for name in ['model.safetensors','rl_agent_config.json','encoder/config.json','tokenizer/tokenizer.json']:
                path=folder/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('{}')
            (folder/'questions.json').write_text(json.dumps({question:{'type':'choice','criteria':['positive','negative','neutral','mixed']}}))
        cls.product_agent=Agent('sentiment','positive');cls.trend_agent=Agent('menu_interest','neutral')
        cls.patches=[patch.object(owner_app,'LAYA_CHECKPOINT',cls.product),
            patch.object(owner_app,'LAYA_TREND_CHECKPOINT',cls.trend),
            patch.object(owner_app,'SENTIMENT_MODEL',object()),
            patch.object(owner_app,'predict_sentiment',return_value='negative'),
            patch.object(owner_app,'load_laya_model',return_value=cls.product_agent),
            patch.object(owner_app,'load_laya_trend_model',return_value=cls.trend_agent)]
        for p in cls.patches:p.start()
        cls.server=owner_app.ThreadingHTTPServer(('127.0.0.1',0),owner_app.Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base='http://127.0.0.1:'+str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()
        for p in reversed(cls.patches):p.stop()
        cls.temp.cleanup()

    def setUp(self):
        self.product_agent.calls.clear();self.trend_agent.calls.clear();self.product_agent.probability=.8

    def request(self, body=None, path='/api/sentiment'):
        req=Request(self.base+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with urlopen(req,timeout=10) as response:return json.load(response)

    def test_indobert_and_product_review_dispatch(self):
        result=self.request({'text':'Rasanya kurang enak.','model':'indobert'})
        self.assertEqual(result['label'],'negative');self.assertEqual(result['task'],'product_sentiment')
        result=self.request({'text':'Rasanya enak.','model':'laya_product'})
        self.assertEqual(result['model'],'Laya Sentimen Produk (lokal)')
        self.assertEqual(self.product_agent.calls[0][0],{'review':'Rasanya enak.'})
        self.assertFalse(self.trend_agent.calls)

    def test_trend_passes_exact_training_state_and_question(self):
        result=self.request({'text':'Rasanya enak.','model':'laya_trend','target_product':'Es Matcha','parent_caption':'Varian baru.'})
        self.assertEqual(result['task'],'menu_interest');self.assertEqual(result['label'],'neutral')
        state,questions=self.trend_agent.calls[0]
        self.assertEqual(json.loads(state['review']),{'target_product':'Es Matcha','parent_caption':'Varian baru.','comment_text':'Rasanya enak.'})
        self.assertIn('menu_interest',questions);self.assertFalse(self.product_agent.calls)

    def test_old_laya_alias_still_routes_to_product(self):
        self.request({'text':'Ulasan produk.','model':'laya'})
        self.assertEqual(len(self.product_agent.calls),1);self.assertFalse(self.trend_agent.calls)

    def test_missing_or_invalid_trend_context_is_rejected_before_inference(self):
        valid={'text':'Aku ingin mencoba.','model':'laya_trend','target_product':'Matcha','parent_caption':'Menu baru.'}
        for field,value in [('target_product',' '),('target_product',3),('target_product','x'*161),
                            ('parent_caption',''),('parent_caption',[]),('parent_caption','x'*2001)]:
            with self.subTest(field=field,value=str(value)[:20]),self.assertRaises(HTTPError) as error:
                self.request({**valid,field:value})
            self.assertEqual(error.exception.code,400)
        self.assertFalse(self.trend_agent.calls)

    def test_options_require_model_files_and_correct_task(self):
        with patch('owner_app.importlib.util.find_spec',return_value=object()):
            config=self.request(path='/api/sentiment/options')
            self.assertTrue(config['indobert_available']);self.assertTrue(config['laya_product_available']);self.assertTrue(config['laya_trend_available'])
            with patch.object(owner_app,'LAYA_TREND_CHECKPOINT',self.product):
                config=self.request(path='/api/sentiment/options');self.assertFalse(config['laya_trend_available'])

    def test_invalid_output_probability_is_service_error(self):
        self.product_agent.probability=float('nan')
        with self.assertRaises(HTTPError) as error:self.request({'text':'Ulasan.','model':'laya_product'})
        self.assertEqual(error.exception.code,503)

    def test_unknown_model_and_non_object_are_bad_requests(self):
        for body in [[],{'text':'Komentar.','model':'unknown'}]:
            with self.assertRaises(HTTPError) as error:self.request(body)
            self.assertEqual(error.exception.code,400)


if __name__=='__main__':unittest.main()
