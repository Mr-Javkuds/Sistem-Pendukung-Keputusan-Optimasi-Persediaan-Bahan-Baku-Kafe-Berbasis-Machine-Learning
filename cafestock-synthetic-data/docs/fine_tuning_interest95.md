# Fine-tuning ketertarikan menu: target di atas 95%

Tanggal eksperimen: 8 November 2026.

[Notebook Kaggle privat](https://www.kaggle.com/code/yasinmuhammadyusuf/cafestock-laya-public-product-sentiment-95)

Eksperimen melanjutkan checkpoint ketertarikan `laya_menu_interest_v1`, bukan
model review produk. Pedoman label tetap: positive tertarik, negative menolak,
neutral arah minat belum jelas, mixed tertarik sekaligus ragu/menolak.

## Data training dan penguncian evaluasi

- Train lama: 1.275 teks, tetap dipertahankan.
- Tambahan train sintetis: 3.840 contoh kontras minat pasti, penolakan eksplisit,
  penilaian/preferensi tanpa arah minat, dan minat disertai keraguan.
- Total train: 5.115 teks; 1.278/1.280/1.278/1.279 per kelas pos/neg/neu/mixed.
- Validation asli tetap 476 teks; digunakan untuk memilih konfigurasi.
- Test lama tetap 478 teks. Karena hasilnya sudah pernah diperiksa, ini dilaporkan
  sebagai regression set, bukan test baru yang belum pernah disentuh.
- Set konfirmasi baru: 960 baris dari 48 keluarga ungkapan, masing-masing
  dipasangkan dengan menu dan konteks berbeda. Dikunci sebelum training.

Augmentasi tidak menyalin komentar validation, test lama atau konfirmasi.
Pemeriksaan fingerprint menggunakan isi komentar yang dinormalisasi. Set
konfirmasi tidak digunakan untuk keputusan kandidat dan hanya dievaluasi sekali
setelah kandidat dipilih. Data dan hash ada di
`datasets/menu_interest_v2_training/training_manifest.json`.

Jumlah baris bukan jumlah ungkapan/manusia independen. Semua contoh tambahan dan
konfirmasi sintetis, masih berbagi domain dan gaya penulis. Skor tinggi pada set
ini belum membuktikan kinerja pada komentar publik nyata.

## Seleksi kandidat

Checkpoint awal yang sama untuk setiap kandidat: output model v1. Maksimal:

Notebook dapat memakai output sumber yang dipasang sebagai Kaggle Input. Bila
lampiran melalui konektor tidak muncul, run privat menerima URL arsip sumber
dari konektor Kaggle melalui variabel `SOURCE_ARCHIVE_URL` atau
`LAYA_SOURCE_ARCHIVE_URL`. URL sementara tidak disimpan dalam kode repository;
untuk menjalankan ulang setelah kedaluwarsa, pasang output sumber secara manual
atau minta URL baru dari konektor. Hash seluruh file checkpoint sumber diperiksa
sebelum training.

| Kandidat | Epoch tambahan | Encoder LR | Head LR | Label smoothing |
|---|---:|---:|---:|---:|
| warm4 | 4 | 1e-5 | 5e-5 | 0,02 |
| warm6 | 6 | 1e-5 | 5e-5 | 0,01 |
| warm8 | 8 | 1,5e-5 | 7,5e-5 | 0,01 |

Micro-batch 2, gradient accumulation 8, seed 42, soft-ce, random option order,
max_len 256, head_max_len 128. Laya menggunakan sebagian train untuk kalibrasi
internal. Validation tidak masuk pembaruan bobot.

Berhenti ketika **accuracy dan macro-F1 validation sama-sama >0,95**. Jika belum
tercapai, lanjut kandidat berikutnya. Kandidat terbaik dipilih berdasarkan nilai
minimum accuracy/macro-F1 validation, kemudian macro-F1 sebagai pembeda. Set
konfirmasi dan test lama tidak ikut seleksi. Hasil konfirmasi boleh di bawah
target; tidak ada perubahan label atau penghapusan prediksi salah agar lolos.

## Output

- `candidate_scores.json`: parameter dan metrik validation setiap kandidat.
- `pretraining_lock.json`: hash holdout sebelum training.
- `selection_frozen.json`: pemilihan sebelum evaluasi holdout.
- `legacy_test_metrics.json` dan prediksi/kesalahan.
- `confirmation_metrics.json` dan prediksi/kesalahan.
- `model_manifest.json`: hasil, provenance dan hash checkpoint.
- `laya_menu_interest_v2.zip`: checkpoint terpilih dan artefak, pada output Kaggle.

Checkpoint v1, dataset pasar v1 dan hasil ablation terdahulu tetap tersimpan.
Eksperimen ini hanya memperbaiki model teks; hasil ablation v1 tidak otomatis
menjadi evaluasi model v2. Model v2 kini tersedia sebagai pilihan Laya Tren Sentimen pada form dashboard.
Seri historis SVM dan peramalan persediaan belum diganti.

## Hasil run selesai

Notebook versi 3 selesai. Checkpoint warm8 terpilih: validation accuracy 94,54% / macro-F1 0,9447; test lama 84,73% / 0,8373; konfirmasi baru 98,85% / 0,9885. Target >95% belum konsisten antar-set. [Laporan lengkap](../reports/menu_interest_v2/report.md).
