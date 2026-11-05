# Tahap 06 — Encoding

196/196 checks passed.

Preprocessing dipelajari dari train saja. Tidak ada classifier/regressor yang dilatih atau skor prediksi yang dihitung.

| Tugas | Train | Validation | Test | Dimensi X |
|---|---:|---:|---:|---:|
| risk | 7470 | 1440 | 1410 | 27 |
| restock_reference | 7470 | 1440 | 1620 | 27 |
| sentiment | 3361 | 664 | 620 | 337 |
| trend | 144 | 28 | 28 | 5 |

Teks: normalisasi NFKC/casefold/whitespace, unigram–bigram TF-IDF, min_df=2, max_features=10000, sublinear TF, smooth IDF, L2 norm, tanpa penghapusan stopword/negasi. Kosakata dan IDF hanya dari train. LabelEncoder sentimen hanya dipelajari dari label train.

Tabular: branch_id/ingredient_id/category_id diperlakukan nominal dengan one-hot. Kategori baru diabaikan oleh encoder dan harus ditandai sebagai masalah cakupan saat serving. Numerik diimputasi median train, lalu StandardScaler train untuk kompatibilitas pembanding linear; Random Forest tidak mensyaratkan scaling. Missing indicator hanya muncul jika ada missing saat fit. Data aktual saat ini lengkap; perilaku missing/unknown diuji terpisah.

ID baris, split, fingerprint, waktu label, target, dan metadata lain tidak masuk X. Risk tetap binary; target regresi tetap satuan aslinya. restock_reference masih meniru aturan baseline dan bukan target pembelian optimal.

## Batas penggunaan
Artefak ini untuk split tetap yang sudah disiapkan. Pada cross-validation/tuning berikutnya, preprocessing harus di-fit ulang di setiap fold training melalui Pipeline, bukan memakai encoder yang sudah melihat semua train untuk mengevaluasi fold awal. TF-IDF dan encoder yang disimpan boleh digunakan untuk prediksi data baru dengan kontrak kolom yang sama.

Data tetap sintetis. Fitur sentimen risiko adalah label aturan referensi, belum prediksi SVM out-of-fold. Memakai sentiment_mean referensi tidak membuktikan alur NLP end-to-end. Transformer joblib hanya boleh dimuat dari artefak proyek yang dipercaya; hash sumber/output tersedia di manifest. Reproduksibilitas diverifikasi pada state dan nilai matriks, bukan menjanjikan byte identik untuk semua format biner lintas versi.

## Pemeriksaan gagal
Tidak ada.

Rincian pemeriksaan, versi, OOV, hash dan state: encoding_report.json. Artefak: ../prepared/06_encoding/. Langkah berikutnya: 07_modeling.