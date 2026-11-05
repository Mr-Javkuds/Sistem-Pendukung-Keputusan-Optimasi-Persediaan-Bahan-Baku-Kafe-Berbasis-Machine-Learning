"""Describe frozen test errors without selecting or changing any model."""
from pathlib import Path
import json
import pandas as pd
from sklearn.metrics import precision_score, recall_score

ROOT = Path(__file__).resolve().parent


def run():
    folder = ROOT/'prepared/07_modeling'
    predictions = pd.read_csv(folder/'D_combined_RandomForest_test_predictions.csv')
    features = pd.read_csv(folder/'risk_predicted_sentiment.csv')
    names = pd.read_csv(ROOT/'output/ingredients.csv').set_index('ingredient_id').ingredient_name
    joined = predictions.merge(features[['risk_row_id', 'on_hand', 'on_order',
        'mean_daily_consumption_14d', 'social_data_available']], on='risk_row_id', validate='one_to_one')
    errors = joined[joined.prediction.ne(joined.target_stockout)].copy()
    errors['error_type'] = errors.target_stockout.map({1: 'false_negative', 0: 'false_positive'})
    errors.to_csv(folder/'risk_error_cases.csv', index=False)
    lines = ['# Analisis kesalahan model test', '',
        'Analisis ini dilakukan setelah model/threshold dibekukan. Tidak digunakan untuk memilih fitur atau parameter ulang.', '',
        '## Sentimen', '',
        'SVM dan Naive Bayes tidak membuat kesalahan pada teks eligible test sintetis. Hasil sempurna konsisten dengan template frasa dan label generator yang sederhana; evaluasi ini belum menguji bahasa informal, ironi, multi-menu, atau Instagram nyata.', '',
        '## Risiko per bahan', '',
        '| Bahan | N test | False negative | False positive | Precision | Recall |',
        '|---|---:|---:|---:|---:|---:|']
    for i, group in joined.groupby('ingredient_id'):
        fn = int(((group.target_stockout == 1) & (group.prediction == 0)).sum())
        fp = int(((group.target_stockout == 0) & (group.prediction == 1)).sum())
        precision = precision_score(group.target_stockout, group.prediction, zero_division=0)
        recall = recall_score(group.target_stockout, group.prediction, zero_division=0)
        lines.append(f'| {names[i]} | {len(group)} | {fn} | {fp} | {precision:.4f} | {recall:.4f} |')
    lines += ['', '## Contoh kasus yang terlewat (false negative)', '',
        '| Waktu keputusan | Cabang | Bahan | Stok | Pesanan berjalan | Skor risiko |', '|---|---|---|---:|---:|---:|']
    for row in errors[errors.error_type.eq('false_negative')].head(5).itertuples():
        lines.append(f'| {row.decision_at} | {row.branch_id} | {names[row.ingredient_id]} | {row.on_hand:.1f} | {row.on_order:.1f} | {row.risk_score:.3f} |')
    importance = pd.read_csv(folder/'permutation_importance.csv').head(5)
    lines += ['', '## Ketergantungan model dan implikasi', '',
        'Lima fitur dengan penurunan AP terbesar saat diacak: ' + ', '.join(importance.feature) + '.',
        'Kasus false negative merupakan kejadian stockout yang labelnya baru diketahui setelah keputusan. Stok saat ini saja tidak menjamin kecukupan bahan selama tujuh hari; pesanan masuk, konsumsi, bahan lain dalam resep dan kebijakan historis ikut menentukan outcome.',
        'False positive dapat menghasilkan prioritas berlebih; skor risiko tidak langsung diubah menjadi jumlah beli. Jumlah beli ditentukan terpisah oleh forecast dan kebijakan stok yang diuji ulang.',
        'Importance mengukur ketergantungan prediksi, bukan penyebab stockout. Kontribusi sentimen harus dibaca bersama ablation D vs E (volume tetap tersedia).', '',
        '[Semua kasus salah](../prepared/07_modeling/risk_error_cases.csv) memuat fitur saat keputusan dan label aktual untuk audit.']
    (ROOT/'reports/error_analysis.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(f'Error analysis: {len(errors)} risk errors recorded; no model changed')


if __name__ == '__main__':
    run()
