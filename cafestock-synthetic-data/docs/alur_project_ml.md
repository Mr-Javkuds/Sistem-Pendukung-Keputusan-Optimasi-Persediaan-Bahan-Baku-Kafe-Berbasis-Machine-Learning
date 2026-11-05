# Alur dan progres proyek ML

[README utama](../../README.md) · [Indeks dokumentasi](README.md) · [Panduan menjalankan](../README.md)

## Status per 5 November 2026

Persiapan data telah direvisi menjadi skenario Semarang; Instagram sintetis
menggantikan ulasan pembelian kafe. Generator, fitur referensi, schema dan
validator tersedia. Tahap 06 encoding sudah dijalankan: TF-IDF serta encoder,
imputer dan scaler dipelajari dari train saja. Matriks tetap terpisah per split;
laporan aktual di reports/encoding_report.md. Tahap 07–11 juga telah dijalankan:
pelatihan/evaluasi, explainability, forecast kebutuhan, replay kebijakan dan
dashboard lokal. Scraper nyata tidak diperlukan dalam lingkup Instagram sintetis.
Hasil pemeriksaan aktual dibaca dari reports/, bukan dianggap sebagai akurasi ML.

✅ Selesai dengan bukti tersimpan di Git · ⬜ Belum dikerjakan.
Checklist menunjukkan penyelesaian tahap, bukan akurasi atau manfaat bisnis.

- [x] **01 — Raw dataset:** input sumber, output sintetis, dan provenance tersedia.
- [x] **02 — Data cleaning:** duplikasi, eligibility, NULL, label, dan waktu diaudit.
- [x] **03 — EDA:** ringkasan serta grafik train tersedia.
- [x] **04 — Feature engineering:** fitur historis dan target dipisahkan.
- [x] **05 — Split 70/15/15:** partisi waktu serta ekspor X/y/metadata tersedia.
- [x] **06 — Encoding:** TF-IDF, one-hot, imputasi/scaling train-only dan matriks tersedia.
- [x] **07 — Modeling:** model utama dan pembanding sudah dilatih.
- [x] **08 — Evaluation:** metrik test, ablation, dan analisis kesalahan tersedia.
- [x] **09 — Explainability:** importance, bobot kata, dan contoh keputusan tersedia.
- [x] **10 — Optimasi pembelian:** forecast kebutuhan dan replay empat kebijakan selesai.
- [x] **11 — Aplikasi pemilik:** dashboard, rekomendasi, alasan, waktu data, dan persetujuan lokal diuji.

### Bukti progres

| Cakupan | Hasil tercatat | Sumber |
|---|---|---|
| Validasi dataset | 374/374 pemeriksaan lulus | [Validasi](../reports/validation_report.md) |
| Tahap 01–05 | 239/239 pemeriksaan lulus | [Audit tahap 01–05](../reports/steps_1_5_audit.md) |
| EDA train | Ringkasan dan grafik tersedia | [EDA](../reports/eda_report.md) |
| Reproduksibilitas generator | 26/26 CSV identik pada dua generasi | [Reproduksibilitas](../reports/reproducibility_report.md) |
| PostgreSQL | Impor dan constraint diperiksa | [Verifikasi PostgreSQL](../reports/postgres_verification.md) |
| Tahap 06 | 196/196 pemeriksaan lulus | [Laporan encoding](../reports/encoding_report.md) |

Hasil ini dibaca dari laporan yang tersedia, bukan pemeriksaan baru atau akurasi
ML. Pernyataan belum ada encoding di laporan tahap 01–05 hanya berlaku untuk
cakupan tahap tersebut. Encoding dikerjakan terpisah pada tahap 06.

### Menjalankan ulang hasil

1. Pertahankan binding data/manifest; jika data berubah, ulangi persiapan dan encoding.
2. Jalankan `train_models.py` untuk tahap 07–09 dan `optimize_inventory.py` untuk tahap 10.
3. Jalankan `owner_app.py` untuk tahap 11, kemudian unit test dan uji browser.

Bukti: [model dan evaluasi](../reports/modeling_report.md),
[optimasi](../reports/optimization_report.md), [aplikasi](aplikasi_pemilik.md),
dan [audit penyelesaian](../reports/completion_report.md).

## Urutan eksperimen

| Tahap | Pekerjaan | Keluaran |
|---|---|---|
| 01_raw_dataset | Simpan transaksi sumber dan konteks Google terpisah; generate Instagram sintetis Semarang | Provenance serta caption/menu/wilayah |
| 02_data_cleaning | Periksa duplikasi teks, label, lokasi unknown, waktu publikasi dan koleksi; catat perlakuan | Dataset siap dianalisis |
| 03_eda | Grafik volume menu per wilayah/bulan, sentimen, konsumsi, stockout dan limbah | Hipotesis, bukan klaim tren nyata |
| 04_feature_engineering | Map menu ke resep/bahan, agregasi bulan yang sudah terkumpul, indeks tren lag, stok/pesanan/pemasok | Fitur point-in-time dan target terpisah |
| 05_split_70_15_15 | Gunakan waktu; sentimen berdasarkan collected_at, risiko berdasarkan decision_at dan purge | Train/validation/test yang sah |
| 06_encoding | Fit TF-IDF dan encoding/imputasi hanya pada train; ID, waktu target dan label bukan input | Pipeline preprocessing |
| 07_modeling | SVM + Naive Bayes pembanding sentimen; Random Forest + Logistic Regression pembanding risiko | Kandidat model |
| 08_evaluation | Pilih parameter pada validation; test final; ablation tren/sentimen dengan budget setara | Metrik dan analisis kesalahan |
| 09_explainability | Periksa kontribusi fitur dan contoh keputusan; bedakan penjelasan model dari aturan restok | Alasan yang dipahami pemilik |
| 10_optimization | Forecast kebutuhan bahan dan replay stok dengan permintaan sama | Kebijakan terpilih pada validation dan hasil test |
| 11_owner_app | Dashboard lokal, ekspor, analisis teks, persetujuan rencana | Aplikasi pemilik diuji HTTP dan Chrome |

## Data dan label

- Sentimen: sentiment_ml_dataset.csv, X=content_text, y=sentiment_label; empat
  kelas positive/neutral/negative/mixed. Jangan masukkan product_id/region_id untuk
  menggantikan pembacaan teks. split=pending berada di luar ketersediaan data saat ini.
  Gunakan training_status=eligible saja; duplikat kanonik dipertahankan pada waktu
  pengambilan paling awal dan kemunculan berikutnya dikeluarkan. text_fingerprint
  serta training_status bukan input model. Prepared X/y/metadata telah dipisahkan
  oleh audit_steps_1_5.py; hasil aktual ada di reports/steps_1_5_audit.md.
- Risiko: inventory_risk_ml_dataset.csv, X sesuai feature_manifest.json,
  y=target_stockout dalam 7 hari di bawah kebijakan historis. Gunakan label_observed=1
  dan split != purged. Jangan menggunakan label_window_end atau target sebagai fitur.
- Jumlah pembelian: baseline_purchase_qty adalah aturan referensi; melatih regresi
  untuk menirunya bukan bukti optimasi dan tidak membuktikan manfaat Instagram.

## Integrasi sentimen tanpa leakage

Fitur di `output/` menggunakan label aturan sebagai sentimen referensi.
Fitur turunan di `prepared/07_modeling/` sudah memakai prediksi SVM kronologis.
Implementasi `train_models.py` membuat prediksi teks dengan expanding-window
out-of-fold pada train, lalu mengagregasikan berdasarkan collected_at yang tersedia
sebelum setiap keputusan. Jangan memakai model yang pernah melihat label test
untuk mengisi fitur train atau menghitung agregat masa lalu.

Teks dengan collected_at sesudah akhir simulasi diberi pending; batch tidak boleh
dipakai retrospektif hanya karena published_at lebih awal. Kosong berarti belum
tersedia, bukan netral. Wilayah cabang lain dan unknown tidak ikut sinyal lokal.
Lakukan audit teks identik antarpartisi dan laporkan keterbatasan template.

## Tahap 07–09 — kontribusi pasar dan evaluasi

Eksperimen A fitur operasional; B=A+tren; C=A+sentimen menu regional; D=A+keduanya.
Untuk membedakan volume pembahasan dari polaritas, bandingkan juga penambahan
sentiment_mean dengan jumlah postingan tetap tersedia pada kedua model.
Gunakan macro F1/per-class precision-recall pada sentimen, serta precision,
recall stockout, F1 dan PR-AUC pada risiko. Ambang dipilih pada validation.
Jika menampilkan persentase risiko, evaluasi kalibrasi terlebih dahulu.

Tren disimulasikan sebagai penggerak komposisi menu dengan lag 7 hari; sentimen
tidak dipaksakan menjadi penggerak permintaan. Manfaat sentimen dapat nol.
Hasil baik pada dataset ini tidak membuktikan sebab-akibat pasar atau performa
NLP Instagram nyata. Explainability (misalnya permutation importance) mengukur
ketergantungan model pada fitur, bukan memastikan sebab-akibat.

## Tahap 10 — implementasi jumlah pembelian/optimasi

Bangun target kebutuhan bahan masa depan dari latent_demand dan resep, bedakan
dari fulfilled sales yang tersensor stockout; dataset target regresi khusus ini
sudah dibuat di `prepared/10_optimization/demand_forecast_dataset.csv`. Bandingkan prediksi kebutuhan dengan rata-rata historis, lalu
terjemahkan menjadi pembelian dengan netting on_hand/on_order, lead time, safety
stock, kemasan, MOQ dan masa simpan. Simulasikan ulang masing-masing kebijakan
dengan permintaan yang sama. Nilai stockout, fill rate, waste dan biaya berdasarkan
asumsi biaya yang ditetapkan. Jangan mengganti rekomendasi pada ledger lama lalu
menganggap hasil stockout lama sebagai hasil kebijakan baru.

## Keluaran untuk pemilik

Cabang/bahan, waktu data, stok, pesanan berjalan, cakupan historis, prediksi risiko,
prioritas, jumlah dan kemasan pembelian, serta alasan. Jumlah baseline ditandai
sebagai aturan, tidak diklaim keluar langsung dari classifier. Pembaruan Instagram
bulanan dapat digunakan bersama stok harian. Persetujuan pembelian tetap di pemilik.
