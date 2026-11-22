"""Retrospective, frozen-Laya feature ablation; keeps production artifacts intact."""
from pathlib import Path
import hashlib
import io
import json
import zipfile
import unicodedata

import joblib
import numpy as np
import pandas as pd
import torch
import yaml
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, classification_report

from optimize_inventory import build_dataset
from src.encoding import fit_tabular
import train_models

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'reports/ablation_forecast_laya'
CHECKPOINT = ROOT / 'local/laya_cafestock_finetuned'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def norm(text):
    return ' '.join(unicodedata.normalize('NFKC', text).casefold().split())


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(6)
    posts = pd.read_csv(ROOT / 'output/sentiment_ml_dataset.csv')
    posts = posts[posts.split.ne('pending')].copy()
    texts = posts.content_text.drop_duplicates().tolist()
    questions = json.loads((CHECKPOINT / 'questions.json').read_text(encoding='utf-8'))
    checkpoint_hashes = {str(p.relative_to(CHECKPOINT)): sha(p)
                         for p in sorted(CHECKPOINT.rglob('*')) if p.is_file()}
    signature = hashlib.sha256(json.dumps([texts, checkpoint_hashes], sort_keys=True).encode()).hexdigest()
    cache_path = OUT / 'laya_text_predictions.json'
    cache = json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() else {}
    if cache.get('signature') != signature:
        cache = {'signature': signature, 'predictions': {}}
    pending = [t for t in texts if t not in cache['predictions']]
    if pending:
        from laya import load
        print('Loading frozen Laya; unique texts:', len(texts), flush=True)
        agent = load(str(CHECKPOINT))
        for start in range(0, len(pending), 32):
            chunk = pending[start:start + 32]
            results = agent.predict_batch([{'review': t} for t in chunk], questions, batch_size=16)
            assert len(results) == len(chunk)
            for text, result in zip(chunk, results):
                answer = result['answers']['sentiment']
                label = answer.get('choice')
                if label not in ('positive', 'negative', 'neutral', 'mixed'):
                    raise ValueError(f'Invalid Laya label: {label}')
                cache['predictions'][text] = label
            cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding='utf-8')
            print(f'Laya {min(start + 32, len(pending))}/{len(pending)}', flush=True)
    posts['prediction'] = posts.content_text.map(cache['predictions'])
    assert posts.prediction.notna().all()
    posts.to_csv(OUT / 'laya_post_predictions.csv', index=False)
    # This aggregation enforces collected_at < decision_at, but the frozen
    # checkpoint itself is NOT a rolling-origin model. Report this distinction.
    original_dest = train_models.DEST
    try:
        train_models.DEST = OUT
        features = train_models.predicted_risk_features(posts)
    finally:
        train_models.DEST = original_dest
    tables = {n: pd.read_csv(ROOT / 'output' / f'{n}.csv') for n in
              ['ingredients', 'suppliers', 'branches', 'recipes', 'recipe_ingredients', 'latent_demand']}
    tables['risk_predicted_sentiment'] = features
    config = yaml.safe_load((ROOT / 'config.yaml').read_text())
    data = build_dataset(tables, config)
    data.to_csv(OUT / 'forecast_dataset_laya.csv', index=False)
    base = ['branch_id', 'ingredient_id', 'mean_daily_consumption_14d', 'weekday', 'month']
    groups = {'A': base, 'B': base + ['market_interest_latest'],
              'C': base + ['menu_sentiment_latest_week', 'social_data_available'],
              'D': base + ['market_interest_latest', 'menu_sentiment_latest_week', 'social_data_available']}
    train = data[data.forecast_split.eq('train')]
    ingredients = tables['ingredients'].set_index('ingredient_id')
    metrics, split_info = [], {}
    for part in ['train', 'validation', 'test']:
        f = data[data.forecast_split.eq(part)]
        split_info[part] = {'rows': len(f), 'start': f.decision_at.min(), 'end': f.decision_at.max()}
    for version, cols in groups.items():
        print('Fitting forecast', version, flush=True)
        model = Pipeline([('preprocessing', fit_tabular(train[cols], ['branch_id', 'ingredient_id'])),
                          ('model', RandomForestRegressor(n_estimators=80, max_depth=12,
                              min_samples_leaf=8, random_state=42, n_jobs=2))])
        model.fit(train[cols], train.target_daily_required)
        joblib.dump(model, OUT / f'RF_Regressor_{version}.joblib')
        for part in ['validation', 'test']:
            f = data[data.forecast_split.eq(part)].copy()
            f['prediction'] = model.predict(f[cols])
            f.to_csv(OUT / f'{version}_{part}_predictions.csv', index=False)
            for ingredient, g in f.groupby('ingredient_id'):
                info = ingredients.loc[ingredient]
                metrics.append({'version': version, 'split': part, 'ingredient_id': int(ingredient),
                    'ingredient': info.ingredient_name, 'unit': info.unit, 'n': len(g),
                    'mae': mean_absolute_error(g.target_daily_required, g.prediction),
                    'rmse': float(np.sqrt(mean_squared_error(g.target_daily_required, g.prediction))),
                    'historical_mae': mean_absolute_error(g.target_daily_required, g.mean_daily_consumption_14d)})
    metrics = pd.DataFrame(metrics)
    metrics.to_csv(OUT / 'metrics_per_ingredient.csv', index=False)
    test = metrics[metrics.split.eq('test')]
    pivot = test.pivot(index='ingredient_id', columns='version', values='mae')
    improvements = (pivot.A - pivot.D) / pivot.A * 100
    # Ratios are dimensionless; raw MAE/RMSE across g, ml and pcs are never pooled.
    summaries = {v: {'mean_mae_ratio_to_A': float((pivot[v] / pivot.A).mean()),
                      'ingredients_better_than_A': int((pivot[v] < pivot.A).sum())} for v in groups}
    # Audit known training-text overlap from the archived Kaggle input.
    with zipfile.ZipFile(ROOT / 'notebooks/cafestock_laya_sentiment_data.zip') as archive:
        known_train = set(pd.read_csv(io.BytesIO(archive.read('train.csv'))).content_text.map(norm))
    overlap = {p: int(posts[posts.split.eq(p)].content_text.map(norm).isin(known_train).sum())
               for p in ['train', 'validation', 'test']}
    text_eval = classification_report(posts.sentiment_label, posts.prediction, output_dict=True, zero_division=0)
    result = {'design': 'retrospective frozen-checkpoint feature ablation; not leakage-free rolling-origin validation',
              'checkpoint_hashes': checkpoint_hashes, 'features': groups, 'splits': split_info,
              'summary_test': summaries, 'known_kaggle_training_text_overlap_by_current_post_split': overlap,
              'sentiment_all_posts_including_training_overlap': text_eval,
              'input_hashes': {n: sha(ROOT / n) for n in ['config.yaml', 'output/sentiment_ml_dataset.csv',
                  'output/inventory_risk_ml_dataset.csv', 'output/latent_demand.csv', 'output/recipe_ingredients.csv']}}
    (OUT / 'results.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    lines = ['# Laporan Ablation Prediksi Kebutuhan Bahan dengan Sentimen Laya', '',
        'Tanggal: 8 November 2026. CafeStock Intelligence, simulasi tiga cabang Semarang.', '',
        '## Ringkasan', '',
        'Eksperimen ini benar-benar menjalankan inferensi checkpoint Laya CafeStock fine-tuned dan empat Random Forest Regressor. '
        'Hasil mengukur kontribusi kelompok fitur pada ramalan kebutuhan bahan, bukan klasifikasi risiko stockout dan bukan evaluasi jumlah pembelian.', '',
        '**Status metodologis: analisis retrospektif eksploratif dengan checkpoint Laya beku. '
        'Hasil belum memenuhi evaluasi end-to-end bebas kebocoran waktu karena Laya tidak dilatih ulang hanya pada batch yang lebih awal dari setiap prediksi historis.**', '',
        '## Pertanyaan penelitian', '',
        'Apakah penambahan tren kategori dan sentimen menu dari Laya menurunkan kesalahan peramalan kebutuhan bahan dibanding fitur dasar?', '',
        '## Desain eksperimen', '',
        '| Versi | Fitur |', '|---|---|',
        '| A | Cabang, bahan, konsumsi rata-rata 14 hari, hari dalam minggu, bulan |',
        '| B | A + indeks tren pasar terbaru |',
        '| C | A + skor sentimen Laya + indikator ketersediaan sosial |',
        '| D | A + tren + skor sentimen Laya + indikator ketersediaan sosial |', '',
        'Seluruh versi memakai 80 pohon, max_depth=12, min_samples_leaf=8, random_state=42. '
        'Parameter ditetapkan mengikuti konfigurasi proyek; tidak dipilih berdasarkan hasil test. Encoder, imputasi, dan scaler di-fit pada train saja. '
        'Ini ablation kelompok fitur untuk regresi; berbeda dari ablation A–E klasifikasi risiko. '
        'C mencakup skor dan ketersediaan, sehingga perbedaannya belum mengisolasi polaritas saja.', '',
        '## Pembentukan target dan fitur', '',
        'Target = rata-rata kebutuhan harian dari permintaan laten menu dikalikan takaran resep selama '
        'min(lead_time + 2, shelf_life) hari. Satuan mengikuti bahan (g/ml/pcs). '
        'Target memakai permintaan simulasi termasuk yang tidak terpenuhi, bukan hanya penjualan.', '',
        'Laya mengklasifikasikan caption menjadi positive, negative, neutral, mixed. Skor masing-masing +1, -1, 0, 0. '
        'Postingan dipetakan ke menu, resep, bahan, wilayah kota dan wilayah cabang. '
        'Agregat memakai minggu publikasi terakhir yang sudah dikumpulkan sebelum keputusan; collected_at harus lebih kecil dari decision_at. '
        'Lokasi unknown dikeluarkan. Tidak ada penggantian label prediksi dengan label generator. '
        'Teks identik diinferensi sekali lalu hasilnya dipakai kembali; event sosial tetap dipertahankan.', '',
        '## Pembagian data', '', '| Split | Baris | Awal keputusan | Akhir keputusan |', '|---|---:|---|---|']
    for part, item in split_info.items():
        lines.append(f'| {part} | {item["rows"]} | {item["start"]} | {item["end"]} |')
    lines += ['', 'Split kronologis mengikuti konfigurasi 70/15/15; jendela target yang melampaui batas partisi dipurge. '
              'Semua versi menggunakan baris dan target yang identik.', '', '## Hasil test per bahan', '',
              'MAE dan RMSE lebih rendah berarti lebih baik. Kolom perubahan = (MAE A - MAE D) / MAE A × 100%; positif berarti D lebih baik.', '',
              '| Bahan | Satuan/hari | MAE A | MAE B | MAE C | MAE D | Perubahan D vs A | RMSE A | RMSE D |',
              '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for i, row in pivot.iterrows():
        g = test[test.ingredient_id.eq(i)].set_index('version')
        info = ingredients.loc[i]
        lines.append(f'| {info.ingredient_name} | {info.unit} | {row.A:.3f} | {row.B:.3f} | {row.C:.3f} | {row.D:.3f} | {improvements[i]:+.2f}% | {g.loc["A", "rmse"]:.3f} | {g.loc["D", "rmse"]:.3f} |')
    lines += ['', '## Interpretasi', '']
    for v in ['B', 'C', 'D']:
        s = summaries[v]
        lines.append(f'- {v}: MAE lebih rendah dari A pada {s["ingredients_better_than_A"]}/{len(pivot)} bahan; '
                     f'rata-rata rasio MAE terhadap A = {s["mean_mae_ratio_to_A"]:.4f} (di bawah 1 lebih baik).')
    lines += ['', f'Rata-rata perubahan relatif MAE per bahan terhadap A: '
              f'B {(summaries["B"]["mean_mae_ratio_to_A"]-1)*100:+.2f}%; '
              f'C {(summaries["C"]["mean_mae_ratio_to_A"]-1)*100:+.2f}%; '
              f'D {(summaries["D"]["mean_mae_ratio_to_A"]-1)*100:+.2f}%. '
              'Pada ringkasan test ini, tren saja (B) memiliki rasio MAE lebih rendah daripada gabungan (D). '
              'Tambahan sentimen belum memberikan perbaikan rata-rata terhadap tren saja, meskipun membantu beberapa bahan. '
              'Peringkat test ini bersifat deskriptif, bukan dasar pemilihan kebijakan deployment.']
    lines += ['', 'Rasio dihitung per bahan lalu dirata-ratakan dengan bobot sama. '
              'MAE mentah dari satuan berbeda tidak dijumlahkan. Tidak ada klaim signifikansi statistik atau sebab-akibat. '
              'A vs B mengukur tambahan tren; A vs C tambahan kelompok sentimen; B vs D tambahan sentimen saat tren tersedia; C vs D tambahan tren saat sentimen tersedia.', '',
              '## Keterbatasan dan audit Laya', '',
              f'- Teks unik diinferensi: {len(texts)}; event/penyebutan non-pending: {len(posts)}.',
              f'- Teks event yang cocok dengan arsip train Kaggle, per split saat ini: {overlap}. '
              'Arsip ini belum mencakup 48 contoh tambahan round 2, sehingga audit overlap bukan daftar lengkap seluruh data fine-tuning.',
              '- Checkpoint Laya menggunakan data train serta evaluasi validation dari eksperimen terdahulu. '
              'Pemakaian checkpoint beku untuk awal periode memungkinkan model telah melihat label dari masa setelah keputusan tersebut. '
              'Pembatasan collected_at pada agregasi tidak mengatasi kebocoran dari pelatihan model teks.',
              '- Karena itu, hasil ini bukan bukti kinerja historis yang dapat dicapai saat itu. '
              'Untuk evaluasi konfirmatori, gunakan checkpoint Laya expanding-window per batch atau latih Laya pada periode terpisah sebelum seluruh periode regresi, lalu bekukan.',
              '- Seluruh transaksi, tren, dan caption sintetis. Pola template dapat membuat klasifikasi mudah. '
              'Sentimen tidak dipaksakan menyebabkan permintaan pada generator; tambahan fitur boleh merugikan performa.',
              '- Belum ada replay pembelian per versi. Perbedaan MAE belum membuktikan penurunan stockout, limbah atau biaya.', '',
              '## Kesimpulan', '',
              'Eksperimen menunjukkan perbedaan akurasi ketika kelompok fitur ditambah pada RF Regressor dengan checkpoint Laya yang sama. '
              'Gunakan hasil per bahan untuk menilai manfaat dan kerugiannya; jangan menyatakan tren dan sentimen selalu meningkatkan prediksi. '
              'Kesimpulan bersifat eksploratif sampai protokol pelatihan Laya kronologis diterapkan.', '',
              '## Reproduksi dan artefak', '',
              'Jalankan dari direktori cafestock-synthetic-data:', '',
              '```powershell', '../.venv/Scripts/python.exe ablation_forecast_laya.py', '```', '',
              '- results.json: parameter, split, hash checkpoint/input, audit overlap, dan ringkasan.',
              '- metrics_per_ingredient.csv: seluruh MAE/RMSE validation/test dan pembanding historis.',
              '- A/B/C/D_validation_predictions.csv dan A/B/C/D_test_predictions.csv: prediksi per baris.',
              '- laya_post_predictions.csv: label generator serta prediksi Laya untuk audit.',
              '- RF_Regressor_A/B/C/D.joblib: model terlatih.',
              '- forecast_dataset_laya.csv dan risk_predicted_sentiment.csv: data turunan eksperimen.', '',
              'Artefak disimpan terpisah; pipeline dan model produksi SVM/IndoBERT/Laya pada dashboard tidak diubah.']
    (OUT / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(summaries, indent=2), flush=True)
    print('Report:', OUT / 'report.md', flush=True)


if __name__ == '__main__':
    run()
