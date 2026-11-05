"""Stage 10: latent-demand forecasting and full FEFO policy replay.

All policies see identical demand and random seed. Safety factors are chosen on
validation only. Historical consumption is recomputed inside each policy replay.
"""
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
import yaml
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from src.encoding import fit_tabular
from src.simulate_inventory import simulate
from src.generate_ml_datasets import temporal_split
from train_models import dump

ROOT = Path(__file__).resolve().parent
DEST = ROOT / 'prepared/10_optimization'
FEATURES = ['branch_id', 'ingredient_id', 'mean_daily_consumption_14d',
            'market_interest_latest', 'menu_sentiment_latest_month',
            'social_data_available', 'weekday', 'month']


def daily_requirements(tables):
    demand = tables['latent_demand'].copy()
    demand['date'] = demand.transaction_at.str[:10]
    links = tables['recipe_ingredients'].merge(tables['recipes'][['recipe_id', 'product_id']], on='recipe_id')
    rows = demand.merge(links[['product_id', 'ingredient_id', 'quantity']], on='product_id')
    rows['required'] = rows.requested_qty * rows.quantity
    return rows.groupby(['branch_id', 'ingredient_id', 'date']).required.sum().to_dict()


def build_dataset(tables, config):
    requirements = daily_requirements(tables)
    rows = tables['risk_predicted_sentiment'].copy()
    targets, ends = [], []
    for row in rows.itertuples():
        horizon = min(int(row.lead_time_days) + 2, int(row.shelf_life_days))
        day = pd.Timestamp(row.decision_at[:10])
        until = day + pd.Timedelta(days=horizon)
        ends.append(str(until.date()))
        targets.append(sum(requirements.get((row.branch_id, row.ingredient_id,
            str((day + pd.Timedelta(days=d)).date())), 0.) for d in range(horizon)) / horizon)
    rows['weekday'] = pd.to_datetime(rows.decision_at.str[:10]).dt.dayofweek
    rows['month'] = pd.to_datetime(rows.decision_at.str[:10]).dt.month
    rows['target_daily_required'] = targets
    rows['target_end_exclusive'] = ends
    # Independent forecast labels: don't inherit the risk target's seven-day purge.
    rows['forecast_split'] = rows.decision_at.str[:10].map(lambda d: temporal_split(d, config))
    for part in ('train', 'validation', 'test'):
        mask = rows.forecast_split.eq(part)
        last = rows.loc[mask, 'decision_at'].str[:10].max()
        rows.loc[mask & rows.target_end_exclusive.gt(str((pd.Timestamp(last) + pd.Timedelta(days=1)).date())), 'forecast_split'] = 'purged'
    return rows


def summarize(result, tables, config, part):
    snapshots = result['inventory_snapshots'].copy()
    snapshots['split'] = snapshots.date.map(lambda d: temporal_split(d, config))
    snapshots = snapshots[snapshots.split.eq(part)]
    first, last = snapshots.date.min(), snapshots.date.max()
    costs = tables['ingredients'].set_index('ingredient_id').unit_cost_idr
    tx = result['transactions'].set_index('transaction_id')
    items = result['transaction_items'].copy()
    dates = items.transaction_id.map(tx.transaction_at).str[:10]
    items = items[dates.between(first, last)]
    requested, fulfilled = float(items.requested_qty.sum()), float(items.fulfilled_qty.sum())
    stockout_rate = float((items.fulfilled_qty < items.requested_qty).mean())
    lost_revenue = float(((items.requested_qty - items.fulfilled_qty) * items.unit_price_idr).sum())
    snapshot_cost = snapshots.ingredient_id.map(costs)
    # Cost of material consumed or wasted during this interval, including opening
    # inventory and excluding terminal stock. Pending orders are not received yet.
    used_cost = float(((snapshots.consumption + snapshots.waste - snapshots.adjustments) * snapshot_cost).sum())
    holding_cost = float((snapshots.closing_stock * snapshot_cost * .001).sum())
    return {'requested_units': requested, 'fulfilled_units': fulfilled,
        'fill_rate': fulfilled / requested, 'stockout_transaction_rate': stockout_rate,
        'waste_cost_idr': float((snapshots.waste * snapshot_cost).sum()),
        'material_cost_idr': used_cost, 'holding_cost_idr': holding_cost,
        'lost_revenue_idr': lost_revenue,
        'objective_cost_idr': used_cost + holding_cost + lost_revenue,
        'minimum_closing_stock': float(snapshots.closing_stock.min())}


def run():
    DEST.mkdir(parents=True, exist_ok=True)
    config = yaml.safe_load((ROOT / 'config.yaml').read_text())
    names = ['ingredients', 'suppliers', 'branches', 'recipes', 'recipe_ingredients', 'latent_demand']
    tables = {name: pd.read_csv(ROOT / 'output' / f'{name}.csv') for name in names}
    tables['risk_predicted_sentiment'] = pd.read_csv(ROOT / 'prepared/07_modeling/risk_predicted_sentiment.csv')
    data = build_dataset(tables, config)
    data.to_csv(DEST / 'demand_forecast_dataset.csv', index=False)
    train = data[data.forecast_split.eq('train')]
    processor = fit_tabular(train[FEATURES], ['branch_id', 'ingredient_id'])
    model = Pipeline([('preprocessing', processor), ('model', RandomForestRegressor(
        n_estimators=80, max_depth=12, min_samples_leaf=8, random_state=42, n_jobs=1))])
    model.fit(train[FEATURES], train.target_daily_required)
    joblib.dump(model, DEST / 'demand_forecaster.joblib')
    forecasting = {}
    for part in ('validation', 'test'):
        frame = data[data.forecast_split.eq(part)].copy()
        frame['prediction'] = model.predict(frame[FEATURES])
        frame.to_csv(DEST / f'{part}_forecast_predictions.csv', index=False)
        # Different ingredient units must not be averaged into one physical MAE.
        forecasting[part] = {str(i): {
            'model_mae': float(mean_absolute_error(g.target_daily_required, g.prediction)),
            'historical_mean_mae': float(mean_absolute_error(g.target_daily_required, g.mean_daily_consumption_14d)),
            'model_rmse': float(np.sqrt(mean_squared_error(g.target_daily_required, g.prediction)))}
            for i, g in frame.groupby('ingredient_id')}
    daily_features = {d: g for d, g in data.groupby(data.decision_at.str[:10])}

    def rates(day, histories, prior):
        frame = daily_features[str(day.date())].copy()
        frame['mean_daily_consumption_14d'] = [float(np.mean(histories[(r.branch_id, r.ingredient_id)][-14:]))
            if histories[(r.branch_id, r.ingredient_id)] else prior[r.ingredient_id] for r in frame.itertuples()]
        predictions = model.predict(frame[FEATURES])
        return {(r.branch_id, r.ingredient_id): float(v) for r, v in zip(frame.itertuples(), predictions)}

    results, replay = {}, {}
    for name, factor in [('baseline', None), ('ML_0.8', .8), ('ML_1.0', 1.), ('ML_1.2', 1.2)]:
        print('Replay policy', name, flush=True)
        inventory_seed = np.random.SeedSequence(config['seed']).spawn(4)[2]
        result = simulate(config, tables, tables['latent_demand'], np.random.default_rng(inventory_seed),
            rate_policy=None if factor is None else rates, safety_factor=factor or 1.)
        results[name] = {p: summarize(result, tables, config, p) for p in ('validation', 'test')}
        assert all(v['minimum_closing_stock'] >= -1e-5 for v in results[name].values())
        for label in ('inventory_snapshots', 'decisions_internal'):
            result[label].to_csv(DEST / f'{name}_{label}.csv', index=False)
        if name == 'baseline':
            # Prove adding the callback did not alter the historical baseline.
            expected = pd.read_csv(ROOT / 'output/inventory_snapshots.csv')
            pd.testing.assert_frame_equal(result['inventory_snapshots'].reset_index(drop=True),
                expected, check_dtype=False, atol=1e-4, rtol=1e-10)
        replay[name] = result['decisions_internal']
    selected = min((n for n in results if n != 'baseline'), key=lambda n: results[n]['validation']['objective_cost_idr'])
    # Compare candidate policy with the baseline using validation, never test.
    deployed = min(('baseline', selected), key=lambda n: results[n]['validation']['objective_cost_idr'])
    recent = replay[deployed].sort_values('decision_at').groupby(['branch_id', 'ingredient_id']).tail(1).copy()
    recent['policy'] = deployed
    recent.to_csv(DEST / 'owner_recommendations.csv', index=False)
    report = {'forecast_features': FEATURES, 'forecasting': forecasting, 'policies': results,
        'selected_ml_policy': selected, 'recommended_policy': deployed,
        'selection_partition': 'validation', 'factors_tested': [.8, 1., 1.2],
        'objective': 'material consumed+wasted+shrinkage cost + daily holding 0.1% of closing stock value + lost sales revenue',
        'assumptions': ['Same latent demand and discrepancy random seed for every replay.',
            'FEFO, lead time, MOQ, package size, shelf life and pipeline stock enforced by shared simulator.',
            'Lost revenue is an assumed shortage penalty, not measured profit. No fixed ordering fee.',
            'Forecast target uses simulated latent demand; a real cafe needs records of unmet demand.',
            'Forecast train excludes target windows beyond its partition; validation selects safety factor.',
            'Policy replay before validation is warm-up; performance is claimed only on held-out test.',
            'Optimization searches three safety factors; it does not prove a global optimum.']}
    dump(ROOT / 'reports/optimization_report.json', report)
    lines = ['# Tahap 10 â€” peramalan kebutuhan dan optimasi kebijakan', '',
        'Target kebutuhan dibentuk dari permintaan laten Ã— resep, bukan penjualan terpenuhi atau jumlah baseline. Target rata-rata harian mencakup min(lead time + 2, masa simpan) hari; jendela lintas split dikeluarkan.',
        'Regresi Random Forest dibandingkan rata-rata konsumsi historis; MAE/RMSE per bahan dalam satuan masing-masing ada di [JSON](optimization_report.json).', '',
        f'Kandidat ML terpilih pada validation: **{selected}**. Kebijakan rekomendasi setelah dibandingkan baseline pada validation: **{deployed}**.', '',
        '| Kebijakan | Fill rate test | Stockout transaksi test | Limbah test (IDR) | Biaya tujuan test (IDR) |', '|---|---:|---:|---:|---:|']
    for name, row in results.items():
        m = row['test']
        lines.append(f"| {name} | {m['fill_rate']:.4f} | {m['stockout_transaction_rate']:.4f} | {m['waste_cost_idr']:.0f} | {m['objective_cost_idr']:.0f} |")
    lines += ['', '## Asumsi dan interpretasi', '', *['- ' + s for s in report['assumptions']], '',
        'Biaya tujuan = biaya bahan terpakai/limbah/selisih + biaya simpan harian 0,1% nilai stok akhir + nilai penjualan tidak terpenuhi. Biaya limbah sudah termasuk biaya bahan, tidak dijumlahkan dua kali. Nilai stok awal dan akhir tidak dianggap habis terpakai.',
        'Semua kebijakan disimulasikan ulang sepanjang periode. Riwayat konsumsi diperbarui dari hasil kebijakannya sendiri, bukan memakai ledger baseline untuk menilai kebijakan baru.',
        'Rekomendasi terakhir berada di [CSV](../prepared/10_optimization/owner_recommendations.csv); belum merupakan pesanan kepada pemasok.']
    (ROOT / 'reports/optimization_report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('Optimization complete:', deployed, flush=True)


if __name__ == '__main__':
    run()
