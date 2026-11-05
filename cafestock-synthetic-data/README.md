# CafeStock Intelligence — Semarang synthetic research data

Generator Python 3.11+ untuk kafe fiktif di Semarang, dengan 3 cabang, 10 produk,
resep, pemasok, permintaan, transaksi, inventori dan pembahasan menu Instagram.
Periode 2025-11-04 s.d. 2026-11-03, WIB, mata uang IDR.

## Jalankan

```powershell
uv venv --python 3.11 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.venv/Scripts/python.exe generate.py --audit-only
.venv/Scripts/python.exe generate.py --verify-reproducibility
.venv/Scripts/python.exe -m src.validate
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

## Bukti pelaksanaan tahap 01–05

Setelah generator dan validasi selesai, jalankan:

```powershell
uv pip install --python .venv/Scripts/python.exe -r requirements-eda.txt
.venv/Scripts/python.exe audit_steps_1_5.py
```

Helper memeriksa hash/relasi, membuat audit cleaning, EDA train, kontrak fitur,
dan ekspor X/y/metadata train–validation–test di `prepared/`. Model belum dilatih.
Renderer grafik dapat memakai interpreter lain yang sudah memiliki matplotlib
dengan `--plot-python path/to/python.exe`; data preparation tetap berjalan pada
Python 3.11+. Artefak grafik menyimpan versi renderer di laporan audit.

Alternatif: buat venv menggunakan Python 3.11+ dan install requirements.txt dengan
pip. Lingkungan yang dipakai dalam workspace ini berada di `../.venv`.
`--config path/config.yaml` mengganti konfigurasi; lokasi output tetap relatif
terhadap generate.py. Generator offline, tanpa API berbayar, dan menimpa output
miliknya. Jangan menganggap perubahan config otomatis merombak basis data lama.

## Data sosial yang menggantikan ulasan

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

## Eksperimen ML

Tahap **06_encoding sudah tersedia**. Pasang dependensi ML dan jalankan:

```powershell
uv pip install --python .venv/Scripts/python.exe -r requirements-ml.txt
.venv/Scripts/python.exe encode.py --verify-reproducibility
.venv/Scripts/python.exe -m unittest discover -s tests -v
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

## PostgreSQL dan validasi

Dari direktori ini, gunakan database kosong yang khusus untuk eksperimen:

```powershell
psql -v ON_ERROR_STOP=1 -d cafestock -f sql/schema.sql -f sql/import.sql
.venv/Scripts/python.exe verify_postgres.py --pg-bin "C:/Program Files/PostgreSQL/18/bin"
```

Helper membuat cluster sementara di 127.0.0.1:55440, mengimpor CSV, membandingkan
jumlah baris, menguji constraint lalu menghentikan server. Direktori diagnostik
sementara dipertahankan. Database sebelumnya tidak dimigrasikan otomatis.

Validator memeriksa PK/FK, stok nonnegatif, ledger/FEFO, konsumsi per resep,
supplier, label, agregat sosial, lokasi unknown, jadwal batch, split ingestion,
dan rekonstruksi independen fitur sebelum keputusan. Laporan terkini ada di
reports/validation_report.md; hasil aktual SQL dan reproduksibilitas dilaporkan
terpisah. Input sumber eksternal tidak digabung seolah-olah bisnis yang sama.
