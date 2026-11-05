# Alur proyek ML — Semarang dan Instagram sintetis

## Status sekarang

Persiapan data telah direvisi menjadi skenario Semarang; Instagram sintetis
menggantikan ulasan pembelian kafe. Generator, fitur referensi, schema dan
validator tersedia. Model SVM/Random Forest, scraper nyata dan dashboard belum dibuat.
Hasil pemeriksaan aktual dibaca dari reports/, bukan dianggap sebagai akurasi ML.

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

Fitur yang digenerate saat ini menggunakan label aturan sebagai sentimen referensi.
Untuk eksperimen SVM end-to-end, buat prediksi teks dengan expanding-window
out-of-fold pada train, lalu agregasikan berdasarkan collected_at yang tersedia
sebelum setiap keputusan. Jangan memakai model yang pernah melihat label test
untuk mengisi fitur train atau menghitung agregat masa lalu.

Teks dengan collected_at sesudah akhir simulasi diberi pending; batch tidak boleh
dipakai retrospektif hanya karena published_at lebih awal. Kosong berarti belum
tersedia, bukan netral. Wilayah cabang lain dan unknown tidak ikut sinyal lokal.
Lakukan audit teks identik antarpartisi dan laporkan keterbatasan template.

## Kontribusi pasar dan evaluasi

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

## Tahap lanjutan jika fokusnya jumlah pembelian/optimasi

Bangun target kebutuhan bahan masa depan dari latent_demand dan resep, bedakan
dari fulfilled sales yang tersensor stockout; dataset target regresi khusus ini
belum dibuat. Bandingkan prediksi kebutuhan dengan rata-rata historis, lalu
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
