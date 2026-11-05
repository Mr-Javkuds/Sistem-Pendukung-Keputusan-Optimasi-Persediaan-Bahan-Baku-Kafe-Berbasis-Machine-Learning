# CafeStock Intelligence

Sistem Pendukung Keputusan Optimasi Persediaan Bahan Baku Kafe Berbasis Machine
Learning Menggunakan Analisis Tren Pasar dan Sentimen Konsumen.

**CafeStock Intelligence — skenario Semarang, Indonesia.** Proyek akademik ini
menyiapkan dataset persediaan kafe serta sinyal pasar tentang menu berdasarkan
wilayah. Semua data operasional dan konten Instagram yang dihasilkan adalah
**sintetis**, bukan observasi bisnis atau hasil scraping Instagram nyata.

## Mulai membaca

1. Pahami ruang lingkup di bawah.
2. Buka [alur dan progres proyek](cafestock-synthetic-data/docs/alur_project_ml.md).
3. Ikuti [panduan menjalankan](cafestock-synthetic-data/README.md).
4. Cari penjelasan data dan laporan melalui [indeks dokumentasi](cafestock-synthetic-data/docs/README.md).

## Progres per 5 November 2026

| Pekerjaan | Status | Bukti / langkah berikutnya |
|---|---|---|
| 01–05: dataset, cleaning, EDA, fitur, split | ✅ Selesai | [Audit 239/239 lulus](cafestock-synthetic-data/reports/steps_1_5_audit.md) |
| 06: encoding | ✅ Selesai | [Laporan 196/196 lulus](cafestock-synthetic-data/reports/encoding_report.md) |
| 07–09: modeling, evaluasi, explainability | ⬜ Belum dikerjakan | Latih model utama dan pembanding |
| Optimasi pembelian dan aplikasi pemilik | ⬜ Belum dikerjakan | Simulasi ulang kebijakan dan integrasi aplikasi |

Status mengacu pada artefak dan laporan, bukan akurasi model. Tahap 01–06
sudah tersedia; pekerjaan berikutnya adalah tahap 07 modeling.

## Ruang lingkup

- Tiga cabang fiktif: Semarang Tengah, Semarang Selatan, dan Banyumanik.
- Tanggal simulasi 2025-11-04 s.d. 2026-11-03; waktu Asia/Jakarta, mata uang IDR.
- Postingan Instagram sintetis berbahasa Indonesia membahas menu, rasa, dan nilai
  produk pada wilayah Semarang. Tidak ada rating atau ulasan kafe Andi/CafeStock.
- Postingan dipetakan melalui menu dan wilayah, bukan melalui transaksi pelanggan.
- Pembaruan sosial bulanan: fitur hanya memakai batch yang sudah dikumpulkan
  sebelum keputusan; lokasi tidak diketahui tidak masuk agregat regional.
- Yelp, customer_reviews, review_aspects dan generator ulasan telah dikeluarkan
  dari versi aktif. Data sumber asli di luar proyek tidak dihapus.
- Model SVM/Random Forest dan aplikasi pemilik belum dilatih/dibuat.
- Tahap 01–05 sudah diaudit dan tahap 06 encoding telah dijalankan dari train saja;
  matriks serta preprocessing tersimpan untuk langkah modeling berikutnya.

## Dokumen

| Tautan | Isi |
|---|---|
| [Panduan generator](cafestock-synthetic-data/README.md) | Cara menjalankan dan memeriksa data |
| [Dataset Instagram Semarang](cafestock-synthetic-data/docs/sentimen_pasar_menu.md) | Struktur, contoh, label dan relasi pasar |
| [Alur proyek ML](cafestock-synthetic-data/docs/alur_project_ml.md) | Checklist progres, bukti, dan langkah berikutnya |
| [Asumsi dan provenance](cafestock-synthetic-data/docs/assumptions.md) | Batas observasi dan simulasi |
| [Audit sumber](cafestock-synthetic-data/reports/source_audit.md) | Pemeriksaan sumber eksternal yang tersisa |
| [Validasi](cafestock-synthetic-data/reports/validation_report.md) | Hasil pemeriksaan data terkini |
| [Audit tahap 01–05](cafestock-synthetic-data/reports/steps_1_5_audit.md) | Sinkronisasi, cleaning, EDA, fitur dan split yang sudah dijalankan |
| [Data siap tahap modeling](cafestock-synthetic-data/prepared/README.md) | X/y/metadata terpisah dan aturan eligibility |
| [Hasil encoding tahap 06](cafestock-synthetic-data/reports/encoding_report.md) | TF-IDF, one-hot, imputasi/scaling train-only dan pemeriksaannya |
| [Artefak encoding](cafestock-synthetic-data/prepared/06_encoding/README.md) | Matriks CSR, target, metadata dan transformer tersimpan |
| [Reproduksibilitas](cafestock-synthetic-data/reports/reproducibility_report.md) | Hash CSV dua generasi |
| [ERD](cafestock-synthetic-data/docs/erd.md) | Relasi operasional dan menu-wilayah |

## Menjalankan

Python 3.11+. Dari akar repository, buat lingkungan sekali lalu jalankan:

```powershell
uv venv --python 3.11 .venv
uv pip install --python .venv/Scripts/python.exe -r cafestock-synthetic-data/requirements.txt -r cafestock-synthetic-data/requirements-eda.txt
Set-Location cafestock-synthetic-data
../.venv/Scripts/python.exe generate.py --verify-reproducibility
../.venv/Scripts/python.exe -m src.validate
../.venv/Scripts/python.exe audit_steps_1_5.py
```

Generator menulis ulang output miliknya. Petunjuk pengujian, encoding,
dan PostgreSQL ada di panduan menjalankan proyek.

`input/` mempertahankan penjualan sumber dan ekspor Google Trends terpisah dari
`output/` sintetis. Harga IDR adalah asumsi, bukan konversi kurs dari harga sumber.
`multiTimeline.csv` adalah sumber matcha Jawa Tengah, bukan pengamatan Semarang
khusus; seri Semarang dalam `market_trends.csv` tetap sintetis.

Spesifikasi `master_prompt.md` dan PDF contoh proposal merupakan referensi awal;
ketentuan NYC/Yelp di sana telah digantikan instruksi pengguna tentang Semarang
dan Instagram sintetis. Hak/ketentuan materi pihak ketiga tetap mengikuti sumbernya.
