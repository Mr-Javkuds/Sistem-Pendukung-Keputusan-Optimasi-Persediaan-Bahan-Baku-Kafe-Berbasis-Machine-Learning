"""Independent checks of chronology, replay constraints and owner HTTP flows."""
from pathlib import Path
import json
import shutil
import tempfile
import threading
import unittest
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import numpy as np
import pandas as pd
import owner_app
from encode import verify_upstream
from src.generate_ml_datasets import temporal_split
import yaml

ROOT = Path(__file__).resolve().parents[1]


class ArtifactTests(unittest.TestCase):
    def test_upstream_sources_still_match_manifests(self):
        verify_upstream(ROOT)

    def test_every_text_prediction_uses_strictly_earlier_labels(self):
        posts = pd.read_csv(ROOT/'prepared/07_modeling/chronological_sentiment.csv')
        known = posts[posts.prediction.notna()]
        self.assertTrue((pd.to_datetime(known.model_training_max_at, utc=True) <
                         pd.to_datetime(known.collected_at, utc=True)).all())
        self.assertFalse(posts.split.eq('pending').any())
        first = posts[posts.collected_at.eq(posts.collected_at.min())]
        self.assertTrue(first.prediction.isna().all())

    def test_risk_predictions_have_observed_test_labels_and_past_signals(self):
        rows = pd.read_csv(ROOT/'prepared/07_modeling/risk_predicted_sentiment.csv')
        known = rows[rows.predicted_social_available_at.notna()]
        self.assertTrue((pd.to_datetime(known.predicted_social_available_at, utc=True) <
                         pd.to_datetime(known.decision_at, utc=True)).all())
        output = pd.read_csv(ROOT/'prepared/07_modeling/D_combined_RandomForest_test_predictions.csv')
        source = rows.set_index('risk_row_id').loc[output.risk_row_id]
        self.assertTrue(source.split.eq('test').all())
        self.assertTrue(source.label_observed.eq(1).all())
        np.testing.assert_equal(source.target_stockout.to_numpy(), output.target_stockout.to_numpy())

    def test_regression_target_independently_matches_latent_demand(self):
        data = pd.read_csv(ROOT/'prepared/10_optimization/demand_forecast_dataset.csv')
        demand = pd.read_csv(ROOT/'output/latent_demand.csv')
        links = pd.read_csv(ROOT/'output/recipe_ingredients.csv').merge(
            pd.read_csv(ROOT/'output/recipes.csv')[['recipe_id','product_id']], on='recipe_id')
        ing = pd.read_csv(ROOT/'output/ingredients.csv').set_index('ingredient_id')
        for row in data.sample(15, random_state=11).itertuples():
            start = row.decision_at[:10]
            selected = demand[demand.branch_id.eq(row.branch_id) & demand.transaction_at.str[:10].ge(start) &
                demand.transaction_at.str[:10].lt(row.target_end_exclusive)]
            recipe = links[links.ingredient_id.eq(row.ingredient_id)].set_index('product_id').quantity
            expected = (selected.requested_qty * selected.product_id.map(recipe).fillna(0)).sum()
            days = (pd.Timestamp(row.target_end_exclusive) - pd.Timestamp(start)).days
            self.assertAlmostEqual(expected/days, row.target_daily_required, places=4)
        config = yaml.safe_load((ROOT/'config.yaml').read_text())
        for part in ('train','validation','test'):
            subset = data[data.forecast_split.eq(part)]
            self.assertTrue(subset.target_end_exclusive.map(lambda d:
                temporal_split(str((pd.Timestamp(d)-pd.Timedelta(days=1)).date()),config)).eq(part).all())

    def test_all_replayed_policies_conserve_inventory_and_respect_packages(self):
        folder = ROOT/'prepared/10_optimization'
        report = json.loads((ROOT/'reports/optimization_report.json').read_text())
        selected = min(report['policies'], key=lambda n: report['policies'][n]['validation']['objective_cost_idr'])
        self.assertEqual(selected, report['recommended_policy'])
        for name in report['policies']:
            stock = pd.read_csv(folder/f'{name}_inventory_snapshots.csv')
            expected = stock.opening_stock+stock.receipts-stock.consumption-stock.waste+stock.adjustments
            np.testing.assert_allclose(expected, stock.closing_stock, atol=1e-4)
            self.assertGreaterEqual(stock.closing_stock.min(), -1e-5)
            continuity = stock.sort_values(['branch_id','ingredient_id','date'])
            previous = continuity.groupby(['branch_id','ingredient_id']).closing_stock.shift()
            np.testing.assert_allclose(continuity.loc[previous.notna(),'opening_stock'], previous.dropna(), atol=1e-4)
            orders = pd.read_csv(folder/f'{name}_decisions_internal.csv')
            orders = orders[orders.baseline_purchase_qty.gt(0)]
            self.assertTrue(orders.baseline_purchase_qty.ge(orders.minimum_order_qty).all())
            np.testing.assert_allclose(orders.baseline_purchase_qty % orders.package_size, 0, atol=1e-5)
        counts = {row['test']['requested_units'] for row in report['policies'].values()}
        self.assertEqual(len(counts), 1)

    def test_default_replay_reproduces_original_inventory(self):
        original = pd.read_csv(ROOT/'output/inventory_snapshots.csv')
        replay = pd.read_csv(ROOT/'prepared/10_optimization/baseline_inventory_snapshots.csv')
        pd.testing.assert_frame_equal(original, replay, check_dtype=False, atol=1e-4, rtol=1e-10)


class OwnerHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = owner_app.ROOT
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        paths = ['output/ingredients.csv','output/branches.csv',
            'prepared/10_optimization/owner_recommendations.csv',
            'prepared/07_modeling/D_combined_RandomForest_test_predictions.csv',
            'prepared/07_modeling/SVM.joblib','reports/modeling_report.json',
            'reports/optimization_report.json','web/index.html']
        for name in paths:
            (cls.root/name).parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,cls.root/name)
        owner_app.ROOT = cls.root
        cls.server = owner_app.ThreadingHTTPServer(('127.0.0.1',0),owner_app.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()
        owner_app.ROOT = cls.original
        cls.temp.cleanup()

    def request(self,path,data=None,origin=None):
        headers={'Content-Type':'application/json'}
        if origin: headers['Origin']=origin
        request=Request(self.base+path, data=None if data is None else json.dumps(data).encode(),headers=headers)
        return urlopen(request, timeout=15)

    def test_page_and_three_branches_and_csv(self):
        with self.request('/') as response:
            self.assertIn('Rencana bahan',response.read().decode())
        for branch in (1,2,3):
            with self.request('/api/overview?branch='+str(branch)) as response:
                data=json.load(response)
                self.assertEqual(len(data['recommendations']),10)
                self.assertTrue(all(r['branch_id']==branch for r in data['recommendations']))
            with self.request('/api/export?branch='+str(branch)) as response:
                self.assertIn('purchase_qty',response.read().decode())

    def test_approval_persists_without_duplicates(self):
        for _ in range(2):
            with self.request('/api/approve',{'branch_id':2}) as response:
                self.assertEqual(json.load(response)['status'],'approved_local_plan')
        saved=json.loads((self.root/'local/approvals.json').read_text())
        self.assertEqual(len(saved),1)
        self.assertEqual(saved[0]['branch_id'],2)

    def test_text_inference_and_invalid_requests(self):
        with self.request('/api/sentiment',{'text':'Matcha enak tetapi harganya mahal.'}) as response:
            self.assertIn(json.load(response)['label'],['positive','negative','neutral','mixed'])
        for path,data,origin,code in [('/api/sentiment',{'text':''},None,400),
            ('/api/overview?branch=999',None,None,400),
            ('/api/approve',{'branch_id':1},'http://untrusted.invalid',403)]:
            with self.assertRaises(HTTPError) as error:
                self.request(path,data,origin)
            self.assertEqual(error.exception.code,code)


if __name__=='__main__':
    unittest.main()
