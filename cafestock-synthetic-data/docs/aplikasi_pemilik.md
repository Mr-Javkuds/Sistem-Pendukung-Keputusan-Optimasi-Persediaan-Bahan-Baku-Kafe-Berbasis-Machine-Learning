# Aplikasi pemilik CafeStock

[README utama](../../README.md) · [Alur proyek](alur_project_ml.md)

Dashboard lokal menampilkan snapshot keputusan terakhir simulasi, bukan data
kafe langsung. Tidak memerlukan akun, API berbayar, atau akses jaringan saat dipakai.

## Menjalankan

Dari folder `cafestock-synthetic-data`, gunakan lingkungan yang sudah dipasang
sesuai panduan proyek:

```powershell
../.venv/Scripts/python.exe owner_app.py
```

Buka [dashboard lokal](http://127.0.0.1:8765). Hentikan server dengan Ctrl+C.
Port alternatif: `owner_app.py --port 8766`. Server hanya menerima koneksi lokal.

## Alur pemilik

1. Pilih salah satu dari tiga cabang Semarang.
2. Periksa waktu snapshot, stok tersedia, pesanan berjalan, jumlah pembelian dan biaya.
3. Buka alasan tiap bahan untuk melihat perkiraan konsumsi, lead time, kemasan,
   MOQ, masa simpan, serta skor risiko historis beserta waktunya.
4. Unduh rencana dalam format CSV jika diperlukan.
5. Tekan **Setujui rencana lokal** untuk mencatat rencana. Data disimpan di
   `local/approvals.json`, diabaikan Git, dan tidak dikirim ke pemasok.
   Persetujuan snapshot/cabang/kebijakan yang sama tidak dibuat dua kali.
6. Coba teks pembahasan menu untuk melihat hasil inferensi SVM.

Jumlah pembelian berasal dari kebijakan stok yang dipilih pada validation. Skor
risiko berasal dari kondisi kebijakan historis pada tanggal yang ditampilkan;
skor tersebut bukan risiko terkalibrasi pada stok hasil simulasi kebijakan baru.
Data awal yang belum memiliki prediksi sentimen historis dinyatakan belum tersedia.

## Memperbarui artefak

```powershell
../.venv/Scripts/python.exe train_models.py
../.venv/Scripts/python.exe optimize_inventory.py
```

Jalankan berurutan setelah persiapan tahap 01–06. Aplikasi membaca model serta
hasil optimasi lokal yang dipercaya; jangan mengganti file joblib dengan file
dari sumber tidak dikenal. Jika file hilang, API menampilkan petunjuk menjalankan pipeline.

## Verifikasi

- Tes HTTP mencakup tiga cabang, ekspor CSV, inferensi teks, persetujuan yang
  tersimpan tanpa duplikasi, input tidak valid, dan penolakan origin lintas situs.
- Uji Chrome memeriksa pilihan cabang, hasil inferensi, unduhan, kesalahan JS,
  dan overflow viewport seluler. Persetujuan diuji pada direktori sementara,
  sehingga pengujian tidak mencatat persetujuan pengguna sebenarnya.

```powershell
../.venv/Scripts/python.exe -m unittest discover -s tests -v
# Opsional: pasang requirements-browser.txt dan Google Chrome untuk uji UI.
../.venv/Scripts/python.exe verify_browser.py
```

Uji UI memerlukan server aktif. Bukti visual: [desktop](../reports/app/desktop.png),
[seluler](../reports/app/mobile.png), dan [hasil uji browser](../reports/app/browser_check.json).
