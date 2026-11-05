# Sistem Pendukung Keputusan Optimasi Persediaan Bahan Baku Kafe Berbasis Machine Learning Menggunakan Analisis Tren Pasar dan Sentimen Konsumen

Proyek akademik **CafeStock Intelligence** untuk menyiapkan dan menguji dukungan
keputusan persediaan bahan baku kafe. Rancangan terbaru menggabungkan data
operasional dengan sentimen pasar tentang menu di media sosial berdasarkan
wilayah serta tren pencarian.

## Status proyek

- Generator Python untuk skenario sintetis tiga cabang CafeStock tersedia.
- 23 CSV tersedia, termasuk katalog, resep, permintaan, transaksi, persediaan,
  pembelian, ulasan sintetis, dan dataset persiapan ML.
- Validasi data: 144/144 pemeriksaan lulus; 23/23 CSV identik pada dua generasi.
- Skema dan impor PostgreSQL telah diuji pada database sementara PostgreSQL 18.1.
- Model ML, scraper media sosial, layanan prediksi, dan dashboard belum dibuat.

Hasil validasi di atas membuktikan konsistensi generator, bukan akurasi prediksi
atau keberhasilan optimasi di kafe nyata.

## Mulai dari sini

| Dokumen | Isi |
|---|---|
| [Panduan generator](cafestock-synthetic-data/README.md) | Instalasi, konfigurasi, generasi ulang dan pemeriksaan |
| [Rancangan sentimen pasar menu](cafestock-synthetic-data/docs/sentimen_pasar_menu.md) | Ruang lingkup terbaru: menu, media sosial dan wilayah |
| [Alur proyek ML](cafestock-synthetic-data/docs/alur_project_ml.md) | Tahapan eksperimen dan batas rancangan awal |
| [Asumsi generator](cafestock-synthetic-data/docs/assumptions.md) | Provenance, resep, simulasi dan keterbatasan |
| [Audit sumber](cafestock-synthetic-data/reports/source_audit.md) | Struktur dan kualitas input yang diperiksa |
| [ERD](cafestock-synthetic-data/docs/erd.md) | Hubungan antar tabel |
| [Kamus data](cafestock-synthetic-data/docs/data_dictionary.md) | Kolom, satuan dan relasi |

## Struktur

```text
.
├── cafestock-synthetic-data/
│   ├── input/        # Salinan sumber eksternal, terpisah dari simulasi
│   ├── src/          # Audit, profiling, generator dan validator
│   ├── output/       # 23 tabel CSV sintetis
│   ├── reports/      # Audit, validasi, hash dan pengujian PostgreSQL
│   ├── docs/         # Rancangan, asumsi, alur dan kamus data
│   ├── sql/          # Skema, impor dan pemeriksaan constraint
│   ├── config.yaml
│   ├── requirements.txt
│   └── generate.py
├── doc/              # Contoh proposal untuk referensi struktur
└── master_prompt.md  # Spesifikasi awal generator
```

## Menjalankan generator

Python 3.11+ diperlukan. Dari direktori `cafestock-synthetic-data`:

```powershell
uv venv --python 3.11 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.venv/Scripts/python.exe generate.py --audit-only
.venv/Scripts/python.exe generate.py --verify-reproducibility
.venv/Scripts/python.exe -m src.validate
```

Parameter ukuran dan periode simulasi dapat diubah melalui `config.yaml`.
Detail alternatif instalasi dan pengujian SQL tersedia pada panduan generator.

## Batas data dan rancangan

Dataset output saat ini masih menggunakan skenario awal ulasan sintetis dari
pembelian CafeStock. Fitur sentimen tersebut belum merupakan hasil scraping
pasar menu. Revisi sumber dan feature engineering mengikuti rancangan terbaru
perlu dikerjakan sebelum eksperimen operasional.

Sumber penjualan, Yelp dan Google Trends berasal dari konteks berbeda dan tidak
digabung sebagai transaksi bisnis nyata yang sama. `geoMap(1).csv` tidak tersedia;
ketiadaan ini dicatat dalam audit. `multiTimeline.csv` merupakan sumber tambahan
tren matcha Jawa Tengah, bukan pengamatan pasar NYC. Simulasi CafeStock memakai
tren sintetis yang diberi provenance tersendiri.

Sumber eksternal dan contoh dokumen mempertahankan hak serta ketentuan sumbernya;
repositori ini tidak memberikan lisensi baru atas materi pihak ketiga. Informasi
URL dan lisensi sumber masih perlu dilengkapi untuk pengumpulan akademik final.
