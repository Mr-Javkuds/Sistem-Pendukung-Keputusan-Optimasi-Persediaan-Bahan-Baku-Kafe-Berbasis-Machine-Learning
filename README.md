# Sistem Pendukung Keputusan Optimasi Persediaan Bahan Baku Kafe Berbasis Machine Learning Menggunakan Analisis Tren Pasar dan Sentimen Konsumen

**CafeStock Intelligence — skenario Semarang, Indonesia.** Proyek akademik ini
menyiapkan dataset persediaan kafe serta sinyal pasar tentang menu berdasarkan
wilayah. Semua data operasional dan konten Instagram yang dihasilkan adalah
**sintetis**, bukan observasi bisnis atau hasil scraping Instagram nyata.

## Ruang lingkup terbaru

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

## Dokumen

| Tautan | Isi |
|---|---|
| [Panduan generator](cafestock-synthetic-data/README.md) | Cara menjalankan dan memeriksa data |
| [Dataset Instagram Semarang](cafestock-synthetic-data/docs/sentimen_pasar_menu.md) | Struktur, contoh, label dan relasi pasar |
| [Alur proyek ML](cafestock-synthetic-data/docs/alur_project_ml.md) | Tahapan eksperimen berikutnya |
| [Asumsi dan provenance](cafestock-synthetic-data/docs/assumptions.md) | Batas observasi dan simulasi |
| [Audit sumber](cafestock-synthetic-data/reports/source_audit.md) | Pemeriksaan sumber eksternal yang tersisa |
| [Validasi](cafestock-synthetic-data/reports/validation_report.md) | Hasil pemeriksaan data terkini |
| [Reproduksibilitas](cafestock-synthetic-data/reports/reproducibility_report.md) | Hash CSV dua generasi |
| [ERD](cafestock-synthetic-data/docs/erd.md) | Relasi operasional dan menu-wilayah |

## Menjalankan

Python 3.11+; dari folder `cafestock-synthetic-data`:

```powershell
uv venv --python 3.11 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.venv/Scripts/python.exe generate.py --verify-reproducibility
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe -m src.validate
```

`input/` mempertahankan penjualan sumber dan ekspor Google Trends terpisah dari
`output/` sintetis. Harga IDR adalah asumsi, bukan konversi kurs dari harga sumber.
`multiTimeline.csv` adalah sumber matcha Jawa Tengah, bukan pengamatan Semarang
khusus; seri Semarang dalam `market_trends.csv` tetap sintetis.

Spesifikasi `master_prompt.md` dan PDF contoh proposal merupakan referensi awal;
ketentuan NYC/Yelp di sana telah digantikan instruksi pengguna tentang Semarang
dan Instagram sintetis. Hak/ketentuan materi pihak ketiga tetap mengikuti sumbernya.
