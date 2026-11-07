# CafeStock Intelligence

Sistem pendukung keputusan untuk perencanaan persediaan bahan baku kafe dengan
ramalan kebutuhan, tren pasar, dan sentimen menu. Proyek akademik ini memakai
skenario **Semarang, Indonesia** dan data simulasi.

> Data transaksi, stok, permintaan, tren Semarang, dan postingan Instagram dalam
> proyek ini sintetis. Hasilnya menjelaskan perilaku simulator; belum membuktikan
> akurasi pada ulasan konsumen atau kondisi pasar nyata.

## Mulai di sini

1. Lihat [alur dan progres proyek](cafestock-synthetic-data/docs/alur_project_ml.md).
2. Ikuti [panduan instalasi dan menjalankan pipeline](cafestock-synthetic-data/README.md).
3. Buka [indeks dokumentasi dan laporan](cafestock-synthetic-data/docs/README.md).
4. Untuk dashboard, ikuti [panduan aplikasi pemilik](cafestock-synthetic-data/docs/aplikasi_pemilik.md).

## Status proyek

Tahap 01–11 tersedia: persiapan data, encoding, evaluasi model, optimasi kebijakan
stok, dan dashboard lokal. Bukti per tahap dirangkum di [laporan penyelesaian](cafestock-synthetic-data/reports/completion_report.md).

| Area | Implementasi | Status dan batas utama |
|---|---|---|
| Analisis pasar | Empat seri mingguan: tren, sentimen, penjualan, nilai stok | Seri pasar Semarang bersifat simulasi |
| Risiko stok | Random Forest dan Logistic Regression dengan ablation tren/sentimen | Dievaluasi pada kebijakan simulasi |
| Rencana pembelian | Forecast kebutuhan dan replay kebijakan dengan MOQ, kemasan, dan lead time | Kebijakan ML_1.2 dipilih pada validation |
| Analisis teks | IndoBERT fine-tuned empat kelas pada form dashboard | Challenge sintetis 2.000 teks: akurasi 54,7%; recall positif 7,6% |
| Dashboard | Analisis, evaluasi, dan rencana pembelian lokal | Persetujuan disimpan lokal; tidak mengirim pesanan |

Hasil sentimen IndoBERT belum layak ditafsirkan sebagai akurasi ulasan nyata.
Lihat [laporan challenge dan per kelas](cafestock-synthetic-data/reports/indobert_experiment/report.md)
serta [prediksi seluruh input](cafestock-synthetic-data/reports/indobert_experiment/predictions_2000.csv).

## Menjalankan dashboard

Gunakan Python 3.11+ dan environment sesuai [panduan instalasi](cafestock-synthetic-data/README.md).
Checkpoint IndoBERT tidak disimpan di GitHub. Untuk menyiapkannya pada clone baru,
jalankan dari `cafestock-synthetic-data`:

```powershell
../.venv/Scripts/python.exe -m pip install -r requirements-ml.txt -r requirements-indobert.txt
../.venv/Scripts/python.exe experiment_indobert.py
../.venv/Scripts/python.exe owner_app.py
```

Fine-tuning memerlukan koneksi internet saat mengunduh base model dan dapat
membutuhkan sekitar 30 menit pada CPU. Sesudah checkpoint lokal tersedia,
buka [http://127.0.0.1:8765](http://127.0.0.1:8765). Detail filter, grafik pembelian,
dan endpoint ada di [panduan aplikasi](cafestock-synthetic-data/docs/aplikasi_pemilik.md).

## Ruang lingkup

- Tiga cabang fiktif: Semarang Tengah, Semarang Selatan, dan Banyumanik.
- Periode simulasi: 2025-11-04 sampai 2026-11-03; waktu WIB dan mata uang IDR.
- Postingan sosial dibuat sintetis; tidak ada scraping Instagram atau data kafe nyata.
- Dashboard dan checkpoint model berjalan lokal. Bobot IndoBERT berada di `tmp/`
  yang diabaikan Git; kode dan instruksi eksperimennya ada di repository.
