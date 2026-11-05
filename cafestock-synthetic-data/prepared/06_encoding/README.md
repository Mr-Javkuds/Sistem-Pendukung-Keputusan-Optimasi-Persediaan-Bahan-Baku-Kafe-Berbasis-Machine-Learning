# Tahap 06 — matriks siap modeling

[Panduan prepared](../README.md) · [Alur dan progres](../../docs/alur_project_ml.md)

> ✅ Selesai per 5 November 2026. Kode, dependensi, laporan, dan matriks tersedia
> di repository. Tahap ini dilanjutkan oleh 07_modeling yang hasilnya ada di `../07_modeling/`.

Artefak dibuat oleh `encode.py --verify-reproducibility`. Tidak ada model prediksi
yang dilatih. TF-IDF, one-hot encoder, imputer dan scaler adalah preprocessing
yang hanya di-fit pada train dari tahap 05.

## Isi setiap folder tugas

- `train_X.npz`, `validation_X.npz`, `test_X.npz`: matriks CSR float32.
- `train_y.npy`, `validation_y.npy`, `test_y.npy`: target sejajar dengan baris X.
- `*_metadata.csv`: salinan byte persis metadata tahap 05; bukan input model.
- `preprocessor.joblib`: transformer yang sudah di-fit pada train.
- `feature_names.json`: urutan kolom matriks hasil encoding.
- `fitted_state.json`: vocabulary/IDF atau kategori, median dan statistik scaler.
- `label_mapping.json`: arti target; sentimen juga mempunyai target_encoder.joblib.

`manifest.json` mencatat hash input dan output, binding generasi, kontrak, versi,
state, dimensi, OOV dan hasil pemeriksaan. Jika generator atau prepared tahap 05
berubah, jalankan audit tahap 01–05 dan encoding ulang; jangan mencampur versi.

## Membaca data

Jalankan dari direktori `cafestock-synthetic-data` setelah memasang requirements-ml.txt:

```python
from scipy import sparse
import numpy as np

X_train = sparse.load_npz('prepared/06_encoding/risk/train_X.npz')
y_train = np.load('prepared/06_encoding/risk/train_y.npy', allow_pickle=False)
assert X_train.shape[0] == len(y_train)
```

Untuk transformasi data baru dengan kolom sesuai kontrak:

```python
import joblib
import pandas as pd
from src.encoding import transform_frame

processor = joblib.load('prepared/06_encoding/sentiment/preprocessor.joblib')
new_posts = pd.DataFrame({'content_text': ['Matcha ini tidak terlalu manis.']})
X_new = transform_frame(processor, new_posts, text=True)
```

Muat joblib hanya dari artefak tepercaya; jangan memuat pickle/joblib dari sumber
acak. Gunakan versi kode, kontrak dan dependensi yang tercatat. Transformasi data
baru tidak memerlukan fit ulang. Kategori cabang/bahan yang belum pernah dikenal
tidak menambah kolom; tandai masalah cakupannya sebelum memberi rekomendasi bisnis.

## Batas

Matriks ini untuk evaluasi pada split tetap. Untuk time-series cross-validation
atau tuning di dalam train, gunakan Pipeline dengan preprocessing baru di setiap
fold; jangan menggunakan transformasi yang sudah mempelajari seluruh train untuk
mengukur fold awal. Sumber sentimen risiko masih label aturan referensi, belum
prediksi model teks out-of-fold. restock_reference adalah pembelajaran aturan
baseline, bukan jumlah optimal atau bukti keberhasilan optimasi.
