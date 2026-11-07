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
from market_analysis import movement_comparison
import yaml

ROOT = Path(__file__).resolve().parents[1]


class ArtifactTests(unittest.TestCase):
    def test_weekly_direction_compares_changes_and_handles_gaps_constants(self):
        rows = [{'interest_index': float(i*i), 'sentiment_score': float(i*i)/100,
                 'sales_units': float(100-i*i), 'stock_value_idr': 50.} for i in range(10)]
        pairs = {(c['left'],c['right']):c for c in movement_comparison(rows)}
        self.assertAlmostEqual(pairs['interest_index','sentiment_score']['r'], 1.)
        self.assertAlmostEqual(pairs['interest_index','sales_units']['r'], -1.)
        self.assertIsNone(pairs['interest_index','stock_value_idr']['r'])
        rows[4]['sentiment_score'] = None
        gaps = movement_comparison(rows)[0]
        self.assertEqual(gaps['paired_changes'], 7)
        self.assertIsNone(movement_comparison(rows[:4])[0]['r'])
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
        cls.original_predict_sentiment = owner_app.predict_sentiment
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        paths = ['output/ingredients.csv','output/branches.csv',
            'prepared/10_optimization/owner_recommendations.csv',
            'prepared/07_modeling/D_combined_RandomForest_test_predictions.csv',
            'prepared/07_modeling/SVM.joblib','reports/modeling_report.json',
            'reports/optimization_report.json','web/index.html', 'web/market_trends.js',
            'web/dashboard.js', 'web/dashboard.css',
            'output/market_trends.csv', 'output/categories.csv', 'output/products.csv',
            'output/recipes.csv', 'output/recipe_ingredients.csv', 'output/transactions.csv',
            'output/transaction_items.csv', 'output/inventory_snapshots.csv',
            'prepared/07_modeling/chronological_sentiment.csv']
        for name in paths:
            (cls.root/name).parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,cls.root/name)
        owner_app.ROOT = cls.root
        # Keep this HTTP contract test independent of downloading/loading the
        # large local IndoBERT checkpoint. The live app loads the real model.
        owner_app.predict_sentiment = lambda text: 'negative' if 'buruk' in text.casefold() else 'positive'
        cls.server = owner_app.ThreadingHTTPServer(('127.0.0.1',0),owner_app.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()
        owner_app.ROOT = cls.original
        owner_app.predict_sentiment = cls.original_predict_sentiment
        cls.temp.cleanup()

    def request(self,path,data=None,origin=None):
        headers={'Content-Type':'application/json'}
        if origin: headers['Origin']=origin
        request=Request(self.base+path, data=None if data is None else json.dumps(data).encode(),headers=headers)
        return urlopen(request, timeout=15)

    def test_page_and_three_branches_and_csv(self):
        with self.request('/') as response:
            self.assertIn('Rencana bahan',response.read().decode())
        for path, content_type in [('/dashboard.css', 'text/css'), ('/dashboard.js', 'text/javascript'),
                                    ('/market_trends.js', 'text/javascript')]:
            with self.request(path) as response:
                self.assertIn(content_type, response.headers['Content-Type'])
                self.assertGreater(len(response.read()), 100)
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

    def test_market_trends_values_periods_and_future_exclusion(self):
        with self.request('/api/trends?branch=1&weeks=4') as response:
            short = json.load(response)
        with self.request('/api/trends?branch=1&weeks=52') as response:
            long = json.load(response)
        self.assertEqual(len(short['categories']), 4)
        for brief, full in zip(short['categories'], long['categories']):
            self.assertEqual(len(brief['series']), 4)
            self.assertEqual(len(full['series']), 52)
            self.assertEqual(brief['latest_index'], full['latest_index'])
            self.assertTrue(all(pd.Timestamp(r['available_at']) < pd.Timestamp(short['decision_at']) for r in full['series']))
            values = [r['interest_index'] for r in full['series']]
            self.assertAlmostEqual(brief['weekly_change_points'], values[-1]-values[-2])
            self.assertAlmostEqual(brief['four_week_change_points'], np.mean(values[-4:])-np.mean(values[-8:-4]))
            self.assertTrue(brief['menus'])
            self.assertTrue(brief['ingredients'])
        path = self.root/'output/market_trends.csv'
        original = path.read_bytes()
        try:
            frame = pd.read_csv(path)
            future = frame.iloc[0].copy()
            future['available_at'] = (pd.Timestamp(short['decision_at'])+pd.Timedelta(days=7)).isoformat()
            future['interest_index'] = 100
            pd.concat([frame, future.to_frame().T], ignore_index=True).to_csv(path, index=False)
            with self.request('/api/trends?branch=1&weeks=4') as response:
                self.assertEqual(json.load(response), short)
        finally:
            path.write_bytes(original)
        with self.assertRaises(HTTPError) as error:
            self.request('/api/trends?weeks=0')
        self.assertEqual(error.exception.code, 400)

    def test_chart_sales_stock_sentiment_match_sources_and_branch(self):
        with self.request('/api/trends?branch=2&weeks=12') as response:
            data = json.load(response)
        category = data['categories'][0]
        point = category['series'][-1]
        products = pd.read_csv(ROOT/'output/products.csv')
        menu_ids = products.loc[products.category_id.eq(category['category_id']), 'product_id']
        transactions = pd.read_csv(ROOT/'output/transactions.csv')
        selected = transactions[transactions.branch_id.eq(2) &
            transactions.transaction_at.str[:10].between(point['sales_window_start'],point['sales_window_end'])]
        items = pd.read_csv(ROOT/'output/transaction_items.csv')
        expected_sales = items.loc[items.transaction_id.isin(selected.transaction_id) & items.product_id.isin(menu_ids),'fulfilled_qty'].sum()
        self.assertEqual(point['sales_units'], expected_sales)
        recipes = pd.read_csv(ROOT/'output/recipes.csv')
        links = pd.read_csv(ROOT/'output/recipe_ingredients.csv')
        ingredients = links.loc[links.recipe_id.isin(recipes.loc[recipes.product_id.isin(menu_ids),'recipe_id']), 'ingredient_id'].unique()
        stock = pd.read_csv(ROOT/'output/inventory_snapshots.csv')
        stock = stock[stock.branch_id.eq(2) & stock.date.eq(point['stock_date']) & stock.ingredient_id.isin(ingredients)]
        costs = pd.read_csv(ROOT/'output/ingredients.csv').set_index('ingredient_id').unit_cost_idr
        self.assertAlmostEqual(point['stock_value_idr'], (stock.closing_stock*stock.ingredient_id.map(costs)).sum())
        posts = pd.read_csv(ROOT/'prepared/07_modeling/chronological_sentiment.csv')
        region = pd.read_csv(ROOT/'output/branches.csv').set_index('branch_id').loc[2,'region_id']
        posts = posts[posts.region_id.isin([1,region]) & posts.product_id.isin(menu_ids) & posts.prediction.notna()]
        posts = posts[pd.to_datetime(posts.collected_at,utc=True)<pd.Timestamp(point['available_at'])]
        batch = posts[posts.collected_at.eq(posts.collected_at.max())]
        expected = (batch.prediction.eq('positive').sum()-batch.prediction.eq('negative').sum())/len(batch)
        self.assertAlmostEqual(point['sentiment_score'], expected)
        self.assertEqual(point['social_post_count'], len(batch))
        self.assertLess(pd.Timestamp(point['sentiment_available_at']), pd.Timestamp(point['available_at']))
        self.assertLess(point['stock_date'], point['week_start'])
        with self.request('/api/trends?branch=2&weeks=52') as response:
            oldest = json.load(response)['categories'][0]['series'][0]
        self.assertIsNone(oldest['sentiment_score'])
        self.assertEqual(oldest['social_post_count'], 0)

    def test_text_inference_and_invalid_requests(self):
        with self.request('/api/sentiment',{'text':'Matchanya buruk.'}) as response:
            result=json.load(response)
            self.assertEqual(result['label'],'negative')
            self.assertEqual(result['model'],'IndoBERT')
        for path,data,origin,code in [('/api/sentiment',{'text':''},None,400),
            ('/api/overview?branch=999',None,None,400),
            ('/api/approve',{'branch_id':1},'http://untrusted.invalid',403)]:
            with self.assertRaises(HTTPError) as error:
                self.request(path,data,origin)
            self.assertEqual(error.exception.code,code)


if __name__=='__main__':
    unittest.main()
