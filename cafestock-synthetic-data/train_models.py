"""Stages 07–09: chronological text predictions, risk ablations and explanations.

Run from this directory with the project's Python environment.
No generated source CSV or prepared stage 01–06 artifact is modified.
"""
from pathlib import Path
import json
import hashlib
import joblib
import numpy as np
import pandas as pd
import yaml
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (classification_report, confusion_matrix, f1_score,
    precision_score, recall_score, average_precision_score, brier_score_loss)
from sklearn.inspection import permutation_importance
from src.encoding import fit_text, fit_tabular
from encode import verify_upstream

ROOT = Path(__file__).resolve().parent
DEST = ROOT / 'prepared/07_modeling'
PARTS = ('train', 'validation', 'test')


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def read_task(task):
    folder = ROOT / 'prepared/05_split_70_15_15' / task
    return {p: {k: pd.read_csv(folder / f'{p}_{k}.csv')
                for k in ('X', 'y', 'metadata')} for p in PARTS}


def text_model(frame, labels, config, bayes=False):
    vectorizer = fit_text(frame, config)
    estimator = MultinomialNB() if bayes else LinearSVC(C=1., random_state=42)
    model = Pipeline([('tfidf', vectorizer), ('model', estimator)])
    # Vectorizer fit is repeated on precisely the same train-only documents.
    model.fit(frame.content_text, labels)
    return model


def chronological_posts(config, final_model, train_end):
    """Strict earlier-batch fitting on eligible train labels, frozen thereafter."""
    rows = pd.read_csv(ROOT / 'output/sentiment_ml_dataset.csv')
    rows = rows[rows.split.ne('pending')].copy()
    rows['prediction'] = pd.Series(index=rows.index, dtype='object')
    rows['model_training_max_at'] = pd.Series(index=rows.index, dtype='object')
    audits = []
    for batch in sorted(rows.collected_at.unique()):
        mask = rows.collected_at.eq(batch)
        past = rows[(rows.collected_at < batch) & rows.split.eq('train') &
                    rows.training_status.eq('eligible')]
        if len(past.sentiment_label.unique()) < 4:
            audits.append({'batch': batch, 'training_rows': len(past), 'status': 'warmup_unavailable'})
            continue
        model = (text_model(past[['content_text']], past.sentiment_label, config)
                 if batch <= train_end else final_model)
        maximum = past.collected_at.max()
        assert maximum < batch
        rows.loc[mask, 'prediction'] = model.predict(rows.loc[mask, 'content_text'])
        rows.loc[mask, 'model_training_max_at'] = maximum
        audits.append({'batch': batch, 'training_rows': len(past),
                       'training_max_at': maximum, 'status': 'predicted'})
    rows.to_csv(DEST / 'chronological_sentiment.csv', index=False)
    dump(DEST / 'chronology_audit.json', audits)
    return rows


def predicted_risk_features(posts):
    risk = pd.read_csv(ROOT / 'output/inventory_risk_ml_dataset.csv')
    branches = pd.read_csv(ROOT / 'output/branches.csv').set_index('branch_id')
    recipes = pd.read_csv(ROOT / 'output/recipes.csv').set_index('recipe_id').product_id
    links = pd.read_csv(ROOT / 'output/recipe_ingredients.csv')
    menus = {i: set(g.recipe_id.map(recipes)) for i, g in links.groupby('ingredient_id')}
    posts = posts[posts.region_id.notna() & posts.prediction.notna()].copy()
    posts['period'] = posts.published_at.str[:7]
    posts['score'] = posts.prediction.map({'positive': 1., 'negative': -1., 'neutral': 0., 'mixed': 0.})
    cache = {}
    records = []
    for row in risk.itertuples():
        region = branches.loc[row.branch_id, 'region_id']
        key = (row.decision_at[:10], region, row.ingredient_id)
        if key not in cache:
            known = posts[(posts.collected_at < row.decision_at) & posts.region_id.isin([1, region]) &
                          posts.product_id.isin(menus[row.ingredient_id])]
            if len(known):
                selected = known[known.period.eq(known.period.max())]
                at = selected.collected_at.max()
                assert at < row.decision_at
                cache[key] = (len(selected), selected.score.mean(), 1,
                    (pd.Timestamp(row.decision_at) - pd.Timestamp(at)).days, at)
            else:
                cache[key] = (0, 0., 0, 0, None)
        records.append(cache[key])
    columns = ['social_post_count_latest_month', 'menu_sentiment_latest_month',
               'social_data_available', 'social_age_days', 'predicted_social_available_at']
    for n, col in enumerate(columns):
        risk[col] = [r[n] for r in records]
    risk.to_csv(DEST / 'risk_predicted_sentiment.csv', index=False)
    return risk


def risk_metrics(y, scores, threshold):
    predicted = (scores >= threshold).astype(int)
    return {'precision': float(precision_score(y, predicted, zero_division=0)),
            'recall': float(recall_score(y, predicted, zero_division=0)),
            'f1': float(f1_score(y, predicted, zero_division=0)),
            'pr_auc_average_precision': float(average_precision_score(y, scores)),
            'brier': float(brier_score_loss(y, scores)),
            'confusion_matrix': confusion_matrix(y, predicted, labels=[0, 1]).tolist()}


def run():
    verify_upstream(ROOT)
    DEST.mkdir(parents=True, exist_ok=True)
    config = yaml.safe_load((ROOT / 'encoding_config.yaml').read_text())
    text = read_task('sentiment')
    text_results = {}
    svm = None
    for name, bayes in [('SVM', False), ('NaiveBayes', True)]:
        model = text_model(text['train']['X'], text['train']['y'].iloc[:, 0], config, bayes)
        joblib.dump(model, DEST / f'{name}.joblib')
        text_results[name] = {}
        for part in ('validation', 'test'):
            y = text[part]['y'].iloc[:, 0]
            predicted = model.predict(text[part]['X'].content_text)
            text_results[name][part] = classification_report(y, predicted, output_dict=True, zero_division=0)
            output = text[part]['metadata'].copy()
            output['actual'] = y
            output['prediction'] = predicted
            output.to_csv(DEST / f'{name}_{part}_predictions.csv', index=False)
        if not bayes:
            svm = model
    print('Text models evaluated; building chronological predictions...', flush=True)
    posts = chronological_posts(config, svm, text['train']['metadata'].collected_at.max())
    risk = predicted_risk_features(posts).set_index('risk_row_id', drop=False)
    prepared = read_task('risk')
    features = json.loads((ROOT / 'docs/feature_manifest.json').read_text())['risk_features']
    social = [c for c in features if c.startswith(('social_', 'menu_sentiment'))]
    market = [c for c in features if c.startswith('market_')]
    operational = [c for c in features if c not in social + market]
    groups = {'A_operational': operational, 'B_trend': operational + market,
              'C_sentiment': operational + social, 'D_combined': features,
              'E_volume_without_polarity': [c for c in features if c != 'menu_sentiment_latest_month']}
    frames = {p: risk.loc[prepared[p]['metadata'].risk_row_id].reset_index(drop=True) for p in PARTS}
    results = {}
    best_pipeline = None
    best_threshold = None
    for group, cols in groups.items():
        for family in ('RandomForest', 'LogisticRegression'):
            candidates = []
            settings = (8, None) if family == 'RandomForest' else (.1, 1.)
            for setting in settings:
                processor = fit_tabular(frames['train'][cols], ['branch_id', 'ingredient_id'])
                estimator = (RandomForestClassifier(n_estimators=150, max_depth=setting,
                    min_samples_leaf=5, class_weight='balanced', random_state=42, n_jobs=2)
                    if family == 'RandomForest' else LogisticRegression(C=setting,
                    class_weight='balanced', max_iter=1500, random_state=42))
                pipeline = Pipeline([('preprocessing', processor), ('model', estimator)])
                pipeline.fit(frames['train'][cols], frames['train'].target_stockout)
                score = pipeline.predict_proba(frames['validation'][cols])[:, 1]
                # Threshold and hyperparameters are selected on validation only.
                threshold = max(np.arange(.1, .91, .05), key=lambda t:
                    f1_score(frames['validation'].target_stockout, score >= t))
                metrics = risk_metrics(frames['validation'].target_stockout, score, threshold)
                candidates.append((metrics['f1'], pipeline, float(threshold), setting, metrics))
            _, pipeline, threshold, setting, validation = max(candidates, key=lambda x: x[0])
            score = pipeline.predict_proba(frames['test'][cols])[:, 1]
            key = group + '_' + family
            results[key] = {'features': cols, 'selected_setting': setting, 'threshold': threshold,
                'validation': validation, 'test': risk_metrics(frames['test'].target_stockout, score, threshold),
                'candidate_count': 2}
            out = frames['test'][['risk_row_id', 'branch_id', 'ingredient_id', 'decision_at', 'target_stockout']].copy()
            out['risk_score'] = score
            out['prediction'] = (score >= threshold).astype(int)
            out.to_csv(DEST / f'{key}_test_predictions.csv', index=False)
            joblib.dump(pipeline, DEST / f'{key}.joblib')
            if group == 'D_combined' and family == 'RandomForest':
                best_pipeline, best_threshold = pipeline, threshold
            print(key, 'test F1', round(results[key]['test']['f1'], 4), flush=True)
    # Hold-out importance explains the frozen primary model, not causal effects.
    importance = permutation_importance(best_pipeline, frames['test'][features],
        frames['test'].target_stockout, scoring='average_precision', n_repeats=5,
        random_state=42, n_jobs=1)
    explanation = pd.DataFrame({'feature': features, 'importance_mean': importance.importances_mean,
                                'importance_std': importance.importances_std}).sort_values('importance_mean', ascending=False)
    explanation.to_csv(DEST / 'permutation_importance.csv', index=False)
    names = svm.named_steps['tfidf'].get_feature_names_out()
    weights = svm.named_steps['model'].coef_
    text_terms = {str(label): names[np.argsort(weights[n])[-12:][::-1]].tolist()
                  for n, label in enumerate(svm.classes_)}
    dump(DEST / 'sentiment_terms.json', text_terms)
    report = {'sentiment': text_results, 'risk': results, 'primary_risk_model': 'D_combined_RandomForest',
        'primary_threshold': best_threshold, 'sentiment_source': 'strict earlier-batch SVM; frozen train model for validation/test',
        'warmup_posts_without_prediction': int(posts.prediction.isna().sum()),
        'limitations': ['Synthetic templates do not establish real Instagram generalization.',
          'Risk labels describe historical inventory policy, not counterfactual policies.',
          'Risk scores are not claimed as calibrated probabilities; Brier scores are reported.',
          'No test-based feature/parameter/threshold selection; permutation importance is descriptive.'],
        'source_manifest_sha256': hashlib.sha256((ROOT / 'reports/generation_manifest.json').read_bytes()).hexdigest()}
    dump(ROOT / 'reports/modeling_report.json', report)
    lines = ['# Tahap 07–09 — model, evaluasi, dan penjelasan', '',
        'Model di-fit pada train; parameter dan threshold risiko dipilih pada validation. Test hanya untuk evaluasi final.',
        'SVM memakai C=1 tetap; Naive Bayes sebagai pembanding. Masing-masing keluarga risiko mendapat dua kandidat per ablation.', '',
        '## Sentimen', '', '| Model | Macro F1 validation | Macro F1 test |', '|---|---:|---:|']
    for name, row in text_results.items():
        lines.append(f"| {name} | {row['validation']['macro avg']['f1-score']:.4f} | {row['test']['macro avg']['f1-score']:.4f} |")
    lines += ['', '## Risiko stockout 7 hari', '', '| Model / fitur | F1 test | Recall test | PR-AUC (AP) test | Brier |', '|---|---:|---:|---:|---:|']
    for name, row in results.items():
        m = row['test']
        lines.append(f"| {name} | {m['f1']:.4f} | {m['recall']:.4f} | {m['pr_auc_average_precision']:.4f} | {m['brier']:.4f} |")
    lines += ['', '## Integrasi dan batas', '',
        'Fitur sentimen stok dihitung ulang dari prediksi SVM. Batch train memakai expanding window berlabel sebelumnya saja; validation/test memakai model train yang dibekukan. Batch awal tanpa empat kelas belum menghasilkan sinyal, bukan diberi label netral.',
        'A=operasional, B=A+tren, C=A+sentimen, D=A+keduanya, E=D tanpa polaritas tetapi volume tetap ada. Kontribusi sentimen dapat nol atau negatif; hasil tidak membuktikan sebab-akibat.',
        '', '## Explainability', '', '[Permutation importance](../prepared/07_modeling/permutation_importance.csv) mengukur penurunan AP pada test, bukan kausalitas. [Kata pendukung SVM](../prepared/07_modeling/sentiment_terms.json) menunjukkan bobot positif tiap kelas.',
        'Prediksi aktual/test tersimpan per model untuk analisis kesalahan. Metrik per kelas, confusion matrix, threshold, kandidat, dan batas lengkap: [JSON](modeling_report.json).',
        'Skor risiko belum dipakai sebagai persentase probabilitas terkalibrasi. Semua hasil berasal dari data sintetis.']
    (ROOT / 'reports/modeling_report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('Stages 07–09 artifacts saved.', flush=True)


if __name__ == '__main__':
    run()
