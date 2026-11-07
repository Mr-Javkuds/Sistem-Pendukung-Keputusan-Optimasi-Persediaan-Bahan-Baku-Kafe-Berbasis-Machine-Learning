"""Descriptive market trends available before the selected decision snapshot."""
import json
import pandas as pd
from itertools import combinations

SERIES = ['interest_index', 'sentiment_score', 'sales_units', 'stock_value_idr']


def movement_comparison(rows):
    """Pearson r on adjacent weekly changes; gaps and constants stay undefined."""
    frame = pd.DataFrame(rows, columns=SERIES, dtype=float)
    changes = frame.diff()
    result = []
    for left, right in combinations(SERIES, 2):
        paired = changes[[left, right]].dropna()
        r = None
        if len(paired) >= 6 and all(paired[c].std() > 1e-12 for c in (left, right)):
            r = float(paired[left].corr(paired[right]))
        result.append({'left': left, 'right': right, 'paired_changes': len(paired), 'r': r,
            'direction': 'belum cukup variasi/data' if r is None else
                         'cenderung sejalan' if r >= .3 else 'cenderung berlawanan' if r <= -.3 else 'hubungan lemah'})
    return result


def market_trend_analysis(root, branch=1, weeks=12):
    if weeks not in (4, 12, 26, 52):
        raise ValueError('Periode harus 4, 12, 26, atau 52 minggu')
    branches = pd.read_csv(root/'output/branches.csv')
    if branch not in branches.branch_id.values:
        raise ValueError('Cabang tidak ditemukan')
    decisions = pd.read_csv(root/'prepared/10_optimization/owner_recommendations.csv')
    cutoff = decisions.loc[decisions.branch_id.eq(branch), 'decision_at'].max()
    if not isinstance(cutoff, str):
        raise ValueError('Snapshot cabang belum tersedia')
    trends = pd.read_csv(root/'output/market_trends.csv')
    trends['time'] = pd.to_datetime(trends.available_at, utc=True)
    known = trends[(trends.time < pd.Timestamp(cutoff)) & trends.region_id.eq(1)]
    categories = pd.read_csv(root/'output/categories.csv')
    products = pd.read_csv(root/'output/products.csv')
    recipes = pd.read_csv(root/'output/recipes.csv')
    links = pd.read_csv(root/'output/recipe_ingredients.csv')
    ingredients = pd.read_csv(root/'output/ingredients.csv')
    transactions = pd.read_csv(root/'output/transactions.csv')
    items = pd.read_csv(root/'output/transaction_items.csv').merge(
        transactions[['transaction_id', 'branch_id', 'transaction_at']], on='transaction_id', validate='many_to_one')
    items = items[items.branch_id.eq(branch)].copy()
    items['date'] = items.transaction_at.str[:10]
    snapshots = pd.read_csv(root/'output/inventory_snapshots.csv')
    snapshots = snapshots[snapshots.branch_id.eq(branch)].copy()
    snapshots = snapshots.merge(ingredients[['ingredient_id', 'unit_cost_idr']], on='ingredient_id')
    snapshots['stock_value_idr'] = snapshots.closing_stock * snapshots.unit_cost_idr
    posts = pd.read_csv(root/'prepared/07_modeling/chronological_sentiment.csv')
    region = branches.set_index('branch_id').loc[branch, 'region_id']
    posts = posts[posts.region_id.isin([1, region]) & posts.prediction.notna()].copy()
    posts['time'] = pd.to_datetime(posts.collected_at, utc=True)
    posts['score'] = posts.prediction.map({'positive': 1., 'negative': -1., 'neutral': 0., 'mixed': 0.})
    first_day, last_day = snapshots.date.min(), snapshots.date.max()
    result = []
    for category in categories.itertuples():
        history = known[known.category_id.eq(category.category_id)].sort_values('time')
        # The period is the last N weekly observations, not N calendar days.
        shown = history.tail(weeks)
        values = history.interest_index
        latest = float(values.iloc[-1]) if len(values) else None
        previous = float(values.iloc[-2]) if len(values) >= 2 else None
        change = latest - previous if previous is not None else None
        recent_mean = float(values.iloc[-4:].mean()) if len(values) >= 4 else None
        prior_mean = float(values.iloc[-8:-4].mean()) if len(values) >= 8 else None
        movement = recent_mean - prior_mean if prior_mean is not None else None
        menus = products[products.category_id.eq(category.category_id)]
        recipe_ids = recipes.loc[recipes.product_id.isin(menus.product_id), 'recipe_id']
        ingredient_ids = links.loc[links.recipe_id.isin(recipe_ids), 'ingredient_id']
        daily_sales = items[items.product_id.isin(menus.product_id)].groupby('date').fulfilled_qty.sum().to_dict()
        category_stock = snapshots[snapshots.ingredient_id.isin(ingredient_ids)].groupby('date').stock_value_idr.sum().to_dict()
        category_posts = posts[posts.product_id.isin(menus.product_id)]
        batches = [(at, g) for at, g in category_posts.groupby('time', sort=True)]
        series = []
        for point in shown.itertuples():
            at = pd.Timestamp(point.available_at)
            day = pd.Timestamp(point.available_at[:10])
            start = day - pd.Timedelta(days=7)
            end = day - pd.Timedelta(days=1)
            complete = str(start.date()) >= first_day and str(end.date()) <= last_day
            units = float(sum(daily_sales.get(str(d.date()), 0) for d in pd.date_range(start, end))) if complete else None
            prior = [(time, group) for time, group in batches if time < at]
            selected_at, selected = prior[-1] if prior else (None, None)
            series.append({'week_start': point.week_start, 'available_at': point.available_at,
                'interest_index': float(point.interest_index),
                'sentiment_score': float(selected.score.mean()) if selected is not None else None,
                'sentiment_available_at': selected_at.isoformat() if selected_at is not None else None,
                'social_post_count': len(selected) if selected is not None else 0,
                'sales_units': units, 'sales_window_start': str(start.date()), 'sales_window_end': str(end.date()),
                'stock_value_idr': float(category_stock[str(end.date())]) if str(end.date()) in category_stock else None,
                'stock_date': str(end.date()) if str(end.date()) in category_stock else None})
        result.append({'category_id': int(category.category_id), 'name': category.category_name,
            'latest_index': latest, 'previous_index': previous, 'weekly_change_points': change,
            'four_week_mean': recent_mean, 'prior_four_week_mean': prior_mean,
            'four_week_change_points': movement,
            'direction': 'belum cukup data' if movement is None else
                         ('naik' if movement > 1 else 'turun' if movement < -1 else 'relatif stabil'),
            'latest_available_at': history.available_at.iloc[-1] if len(history) else None,
            'series': series, 'comparisons': movement_comparison(series),
            'menus': menus.product_name.tolist(),
            'ingredients': ingredients.loc[ingredients.ingredient_id.isin(ingredient_ids), 'ingredient_name'].tolist()})
    modeling = json.loads((root/'reports/modeling_report.json').read_text())
    return {'city': 'Semarang', 'scope': 'Sinyal pasar kota yang sama digunakan oleh ketiga cabang.',
        'decision_at': cutoff, 'weeks': weeks, 'source': 'Seri simulasi pasar Semarang',
        'index_description': 'Indeks 0–100; perubahan dinyatakan dalam poin indeks, bukan jumlah penjualan.',
        'comparison_description': 'Tren pada tanggal pengamatan; sentimen dari batch SVM terbaru yang sudah tersedia (bulanan); penjualan tujuh hari sebelumnya; nilai stok historis akhir hari sebelumnya. Stok memakai nilai IDR agar g/ml/porsi tidak dijumlahkan. Bahan bersama dihitung sekali per kategori, sehingga kategori tidak boleh dijumlahkan.',
        'categories': result, 'model_comparison': {
            'operational_f1': modeling['risk']['A_operational_RandomForest']['test']['f1'],
            'with_trend_f1': modeling['risk']['B_trend_RandomForest']['test']['f1'],
            'description': 'Perbandingan test model risiko stok: fitur operasional vs operasional + tren. Ini bukan bukti sebab-akibat.'}}
