"""Behavior checks for monthly availability, location isolation and independent posts."""
import copy
import unittest
import numpy as np
import pandas as pd
from src.generate_recipes import generate as catalog
from src.generate_social import generate,aggregate,monthly_collection
from src.generate_ml_datasets import generate as features

class SocialPipelineTests(unittest.TestCase):
    def setUp(self):
        self.config={'seed':42,'start_date':'2025-11-25','end_date':'2025-12-04',
                     'timezone':'Asia/Jakarta','mean_daily_social_posts':30,'evaluation_horizon_days':7}

    def test_monthly_collection_not_retroactive(self):
        result=monthly_collection('2025-11-30T23:59:00+07:00','Asia/Jakarta')
        self.assertEqual(result.isoformat(),'2025-12-01T07:00:00+07:00')

    def test_synthetic_discussion_independent_of_sales(self):
        a=catalog(); b=catalog(); b['transaction_items']=pd.DataFrame({'rating':[1,5]})
        first=generate(self.config,a,np.random.default_rng(42))
        second=generate(self.config,b,np.random.default_rng(42))
        pd.testing.assert_frame_equal(first['social_posts'],second['social_posts'])
        self.assertFalse(first['social_posts'].content_text.str.contains('CafeStock').any())
        self.assertTrue(first['social_posts'].source_url.isna().all())

    def fixture(self):
        tables=catalog(); tables.update(generate(self.config,tables,np.random.default_rng(42)))
        tables['menu_market_signals']=aggregate(tables)
        tables['transactions']=pd.DataFrame(columns=['transaction_id','branch_id','transaction_at'])
        tables['transaction_items']=pd.DataFrame(columns=['transaction_item_id','transaction_id','product_id','fulfilled_qty'])
        tables['stockout_events']=pd.DataFrame(columns=['stockout_event_id','transaction_item_id','ingredient_id','event_at'])
        tables['market_trends']=pd.DataFrame([
            (i,1,i,'2025-11-01','2025-11-01T00:00:00+07:00',50.,'synthetic') for i in range(1,5)],
            columns=['trend_id','region_id','category_id','week_start','available_at','interest_index','provenance'])
        rows=[]
        # Milk in two branches before ingestion (Dec 1 05:00) and after it (Dec 2).
        for j,(branch,day) in enumerate([(1,'2025-12-01'),(1,'2025-12-02'),(2,'2025-12-02')],1):
            rows.append((j,branch,2,day+'T05:00:00+07:00',5,1000.,500.,0.,1,5,1000,2000,2000.))
        tables['decisions_internal']=pd.DataFrame(rows,columns=['decision_id','branch_id','ingredient_id','decision_at',
            'history_days','mean_daily_consumption_14d','on_hand','on_order','lead_time_days','shelf_life_days',
            'package_size','minimum_order_qty','baseline_purchase_qty'])
        return tables

    def test_batch_gate_and_branch_district_scope(self):
        tables=self.fixture(); original=copy.deepcopy(tables)
        features(self.config,tables)
        result=tables['restock_decision_dataset'].set_index('decision_id')
        self.assertEqual(result.loc[1,'social_post_count_latest_month'],0)
        self.assertEqual(result.loc[1,'social_data_available'],0)
        self.assertGreater(result.loc[2,'social_post_count_latest_month'],0)
        # Inject positive sentiment into unknown-location and another district only.
        region_by_post=original['social_posts'].set_index('post_id').region_id
        ids=original['menu_mentions'].post_id.map(region_by_post)
        mask=ids.isna()|ids.eq(3)  # branch 1 is region 2, so these are not its market.
        original['menu_mentions'].loc[mask,'sentiment_label']='positive'
        original['menu_market_signals']=aggregate(original)
        features(self.config,original)
        changed=original['restock_decision_dataset'].set_index('decision_id')
        self.assertEqual(result.loc[2,'menu_sentiment_latest_month'],changed.loc[2,'menu_sentiment_latest_month'])
        self.assertEqual(result.loc[2,'social_post_count_latest_month'],changed.loc[2,'social_post_count_latest_month'])

    def test_later_batch_cannot_change_past_features(self):
        tables=self.fixture(); modified=copy.deepcopy(tables)
        post_dates=modified['social_posts'].set_index('post_id').published_at
        future=modified['menu_mentions'].post_id.map(post_dates).str.startswith('2025-12')
        modified['menu_mentions'].loc[future,'sentiment_label']='negative'
        modified['menu_market_signals']=aggregate(modified)
        features(self.config,tables); features(self.config,modified)
        cols=['social_post_count_latest_month','menu_sentiment_latest_month','social_available_at']
        pd.testing.assert_frame_equal(tables['restock_decision_dataset'][cols],modified['restock_decision_dataset'][cols])

if __name__=='__main__': unittest.main()
