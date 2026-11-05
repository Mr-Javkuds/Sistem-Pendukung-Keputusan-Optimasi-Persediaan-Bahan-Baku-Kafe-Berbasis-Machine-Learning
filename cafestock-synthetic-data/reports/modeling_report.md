# Tahap 07–09 — model, evaluasi, dan penjelasan

Model di-fit pada train; parameter dan threshold risiko dipilih pada validation. Test hanya untuk evaluasi final.
SVM memakai C=1 tetap; Naive Bayes sebagai pembanding. Masing-masing keluarga risiko mendapat dua kandidat per ablation.

## Sentimen

| Model | Macro F1 validation | Macro F1 test |
|---|---:|---:|
| SVM | 1.0000 | 1.0000 |
| NaiveBayes | 1.0000 | 1.0000 |

## Risiko stockout 7 hari

| Model / fitur | F1 test | Recall test | PR-AUC (AP) test | Brier |
|---|---:|---:|---:|---:|
| A_operational_RandomForest | 0.7591 | 0.9152 | 0.7002 | 0.2398 |
| A_operational_LogisticRegression | 0.7486 | 0.8969 | 0.6503 | 0.2544 |
| B_trend_RandomForest | 0.7570 | 0.9026 | 0.6930 | 0.2421 |
| B_trend_LogisticRegression | 0.7422 | 0.8706 | 0.6536 | 0.2522 |
| C_sentiment_RandomForest | 0.7583 | 0.9003 | 0.6709 | 0.2555 |
| C_sentiment_LogisticRegression | 0.7494 | 0.8958 | 0.6387 | 0.2634 |
| D_combined_RandomForest | 0.7753 | 0.9427 | 0.6876 | 0.2466 |
| D_combined_LogisticRegression | 0.7527 | 0.9084 | 0.6488 | 0.2580 |
| E_volume_without_polarity_RandomForest | 0.7468 | 0.8648 | 0.6824 | 0.2481 |
| E_volume_without_polarity_LogisticRegression | 0.7359 | 0.8362 | 0.6454 | 0.2576 |

## Integrasi dan batas

Fitur sentimen stok dihitung ulang dari prediksi SVM. Batch train memakai expanding window berlabel sebelumnya saja; validation/test memakai model train yang dibekukan. Batch awal tanpa empat kelas belum menghasilkan sinyal, bukan diberi label netral.
A=operasional, B=A+tren, C=A+sentimen, D=A+keduanya, E=D tanpa polaritas tetapi volume tetap ada. Kontribusi sentimen dapat nol atau negatif; hasil tidak membuktikan sebab-akibat.

## Explainability

[Permutation importance](../prepared/07_modeling/permutation_importance.csv) mengukur penurunan AP pada test, bukan kausalitas. [Kata pendukung SVM](../prepared/07_modeling/sentiment_terms.json) menunjukkan bobot positif tiap kelas.
Prediksi aktual/test tersimpan per model untuk analisis kesalahan. Metrik per kelas, confusion matrix, threshold, kandidat, dan batas lengkap: [JSON](modeling_report.json).
Skor risiko belum dipakai sebagai persentase probabilitas terkalibrasi. Semua hasil berasal dari data sintetis.
