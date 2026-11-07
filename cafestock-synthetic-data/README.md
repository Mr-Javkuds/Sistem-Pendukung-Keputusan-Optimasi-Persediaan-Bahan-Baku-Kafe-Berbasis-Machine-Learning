# Panduan menjalankan CafeStock Intelligence

[README utama](../README.md) · [Alur dan progres](docs/alur_project_ml.md) · [Indeks dokumentasi](docs/README.md)

Proyek simulasi Python 3.11+ untuk tiga cabang kafe fiktif di Semarang. Alurnya:
generator dan pemeriksaan data → fitur dan split waktu → model → replay persediaan
→ dashboard. Transaksi, stok, tren, dan pembahasan menu Instagram bersifat sintetis.

## Jalur cepat

| Tujuan | Mulai dari |
|---|---|
| Menjalankan ulang data dan audit | Bagian 1–2 di bawah |
| Memahami dataset dan batasnya | [Data sosial](#3-pahami-data-sosial) dan [asumsi](docs/assumptions.md) |
| Menjalankan modeling dan optimasi | [Encoding dan eksperimen ML](#4-encoding-dan-aturan-eksperimen-ml) |
| Menjalankan dashboard | [Panduan aplikasi pemilik](docs/aplikasi_pemilik.md) |
| Melihat bukti hasil | [Indeks laporan](docs/README.md) |

## 1. Siapkan lingkungan

Perintah berikut dijalankan dari folder `cafestock-synthetic-data`. Lingkungan
Python disimpan di akar repository (`../.venv`), sesuai workspace saat ini.
Jika lingkungan sudah ada, lewati pembuatan venv.

```powershell
uv venv --python 3.11 ../.venv
uv pip install --python ../.venv/Scripts/python.exe -r requirements.txt -r requirements-eda.txt
../.venv/Scripts/python.exe generate.py --audit-only
../.venv/Scripts/python.exe generate.py --verify-reproducibility
../.venv/Scripts/python.exe -m src.validate
../.venv/Scripts/python.exe -m unittest discover -s tests -v
```

## 2. Jalankan persiapan tahap 01–05

Setelah generator dan validasi selesai, jalankan:

```powershell
uv pip install --python ../.venv/Scripts/python.exe -r requirements-eda.txt
../.venv/Scripts/python.exe audit_steps_1_5.py
```

Helper memeriksa hash/relasi, membuat audit cleaning, EDA train, kontrak fitur,
dan ekspor X/y/metadata train–validation–test di `prepared/`. Model belum dilatih oleh helper ini; pelatihan dilakukan terpisah pada tahap 07.
Renderer grafik dapat memakai interpreter lain yang sudah memiliki matplotlib
dengan `--plot-python path/to/python.exe`; data preparation tetap berjalan pada
Python 3.11+. Artefak grafik menyimpan versi renderer di laporan audit.

Alternatif: buat venv menggunakan Python 3.11+ dan install requirements.txt dengan
pip. Lingkungan yang dipakai dalam workspace ini berada di `../.venv`.
`--config path/config.yaml` mengganti konfigurasi; lokasi output tetap relatif
terhadap generate.py. Generator offline, tanpa API berbayar, dan menimpa output
miliknya. Jangan menganggap perubahan config otomatis merombak basis data lama.

## 3. Pahami data sosial

| File | Isi |
|---|---|
| output/regions.csv | Kota Semarang dan tiga wilayah cabang |
| output/social_posts.csv | Caption Instagram sintetis, waktu publikasi/koleksi, wilayah dan provenance |
| output/menu_mentions.csv | Hubungan postingan–menu dan label sentimen menu |
| output/menu_aspects.csv | Label aspek taste/value; mixed mempunyai aspek berlawanan |
| output/menu_market_signals.csv | Ringkasan menu–wilayah–bulan yang tersedia saat batch dikumpulkan |
| output/sentiment_ml_dataset.csv | Teks dan label untuk eksperimen, split menurut collected_at |
| output/restock_decision_dataset.csv | Fitur operasional dan sinyal menu regional yang tersedia sebelum keputusan |
| output/inventory_risk_ml_dataset.csv | Fitur dan target stockout 7 hari |

platform bernilai instagram, tetapi provenance selalu synthetic. Tidak ada akun
Instagram nyata, URL nyata, geotag terverifikasi, maupun klaim hasil scraping.
source_url kosong, source_post_key berawalan SIM-IG-SMG-. Teks tidak terkait rating,
transaksi pelanggan atau penilaian sebuah kafe. Angka sosial yang dihasilkan bukan
ukuran popularitas menu nyata di Semarang.

Postingan satu bulan dikumpulkan pada tanggal 1 bulan berikutnya pukul 07:00 WIB.
Keputusan stok pukul 05:00 tidak boleh memakai batch pukul 07:00 hari yang sama.
Data publikasi terminal yang batch-nya belum tersedia mendapat split=pending di
dataset sentimen. Fitur stok memakai bulan publikasi terakhir yang sudah terkumpul,
menu yang memakai bahan tersebut, serta wilayah cabang dan kota Semarang.
Lokasi unknown tetap NULL dan dikeluarkan dari agregat regional.

## 4. Encoding dan aturan eksperimen ML

Tahap **06_encoding sudah selesai**; kode, dependensi, laporan, dan matriks
tersedia di repository. Setelah audit tahap 01–05, jalankan:

```powershell
uv pip install --python ../.venv/Scripts/python.exe -r requirements-ml.txt
../.venv/Scripts/python.exe encode.py --verify-reproducibility
../.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Hasilnya di `prepared/06_encoding/`: TF-IDF sentimen, one-hot kategori dan
imputasi/scaling numerik untuk fitur tabular, label mapping, serta matriks
train/validation/test yang terpisah. Semua preprocessing di-fit pada train saja;
hasil validasi dan versi tersimpan di `reports/encoding_report.md` dan JSON-nya.
Tidak ada SVM/Random Forest atau model prediksi lain yang dilatih pada tahap ini.

Gunakan allowlist docs/feature_manifest.json. Untuk sentimen, X=content_text dan
y=sentiment_label. Label dibuat oleh aturan penyusunan teks, bukan prediksi model.
Gunakan hanya `training_status=eligible` untuk model sentimen. Fingerprint teks
NFKC/casefold/whitespace mempertahankan kemunculan yang paling awal dikumpulkan;
kemunculan ulang/konflik yang lebih baru dikeluarkan, tanpa memindahkan split.
Kolom fingerprint dan status hanya untuk audit, bukan fitur model. Postingan mentah
dan agregat event tidak dihapus karena beberapa event sintetis bisa mempunyai
caption identik; ini bukan implementasi pendeteksi spam Instagram nyata.
Untuk risiko, y=target_stockout. Buang split=purged dan gunakan label_observed=1
untuk evaluasi risiko; dataset sentimen menggunakan split sendiri dan mengecualikan
pending. Fit TF-IDF, encoding/imputasi pada train saja.

Sentimen di tabel risiko saat ini adalah sinyal referensi berlabel aturan. Untuk
alur end-to-end, bangun agregat dari prediksi model teks secara kronologis tanpa
leakage. Konten sintetis mempunyai pola template: skor NLP tinggi tidak membuktikan
kinerja pada Instagram nyata. Sentimen tidak dipaksakan menyebabkan permintaan;
kontribusinya harus diuji dengan ablation.

Jumlah pembelian baseline ditentukan oleh stok, konsumsi historis, lead time,
kemasan dan MOQ, bukan oracle atau jumlah optimal. Penilaian kebijakan baru perlu
backtest ulang, bukan sekadar mengganti jumlah pesanan pada ledger yang sama.

## 5. PostgreSQL dan validasi

Dari direktori ini, gunakan database kosong yang khusus untuk eksperimen:

```powershell
psql -v ON_ERROR_STOP=1 -d cafestock -f sql/schema.sql -f sql/import.sql
../.venv/Scripts/python.exe verify_postgres.py --pg-bin "C:/Program Files/PostgreSQL/18/bin"
```

Helper membuat cluster sementara di 127.0.0.1:55440, mengimpor CSV, membandingkan
jumlah baris, menguji constraint lalu menghentikan server. Direktori diagnostik
sementara dipertahankan. Database sebelumnya tidak dimigrasikan otomatis.

Validator memeriksa PK/FK, stok nonnegatif, ledger/FEFO, konsumsi per resep,
supplier, label, agregat sosial, lokasi unknown, jadwal batch, split ingestion,
dan rekonstruksi independen fitur sebelum keputusan. Laporan terkini ada di
reports/validation_report.md; hasil aktual SQL dan reproduksibilitas dilaporkan
terpisah. Input sumber eksternal tidak digabung seolah-olah bisnis yang sama.

## 6. Modeling, evaluasi, optimasi, dan aplikasi (tahap 07–11)

Setelah tahap 01–06 selesai, jalankan berurutan:

```powershell
uv pip install --python ../.venv/Scripts/python.exe -r requirements-ml.txt
../.venv/Scripts/python.exe train_models.py
../.venv/Scripts/python.exe optimize_inventory.py
../.venv/Scripts/python.exe analyze_results.py
../.venv/Scripts/python.exe -m unittest discover -s tests -v
../.venv/Scripts/python.exe -m pip install -r requirements-indobert.txt
../.venv/Scripts/python.exe experiment_indobert.py
../.venv/Scripts/python.exe owner_app.py
```

Buka [dashboard lokal](http://127.0.0.1:8765). Pelatihan menulis model, prediksi,
fitur sentimen historis, dan penjelasan di `prepared/07_modeling/`. Optimasi
menulis forecast serta replay stok di `prepared/10_optimization/`.
Eksperimen IndoBERT membuat checkpoint `../tmp/indobert-cafestock-fourclass` untuk
form teks; jalankan setelah train/test challenge tersedia. Fine-tuning memerlukan
internet saat mengunduh base model dan memakan sekitar 30 menit pada CPU.
Baca [laporan model](reports/modeling_report.md), [laporan optimasi](reports/optimization_report.md),
[petunjuk aplikasi](docs/aplikasi_pemilik.md), dan [bukti penyelesaian](reports/completion_report.md).
Data sumber dan artefak tahap 01–06 tidak ditimpa oleh kedua script ini.
