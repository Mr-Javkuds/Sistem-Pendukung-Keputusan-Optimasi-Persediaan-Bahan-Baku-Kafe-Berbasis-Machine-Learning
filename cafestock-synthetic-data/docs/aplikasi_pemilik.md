# Aplikasi pemilik CafeStock

[README utama](../../README.md) · [Alur proyek](alur_project_ml.md)

Dashboard lokal menampilkan snapshot keputusan terakhir simulasi, bukan data
kafe langsung. Tidak memerlukan akun, API berbayar, atau akses jaringan saat dipakai.

## Menjalankan

Dari folder `cafestock-synthetic-data`, pasang dependensi (sekali per environment),
buat checkpoint IndoBERT lokal, lalu jalankan aplikasi:

```powershell
../.venv/Scripts/python.exe -m pip install -r requirements-ml.txt -r requirements-indobert.txt
../.venv/Scripts/python.exe experiment_indobert.py
../.venv/Scripts/python.exe owner_app.py
```

Checkpoint disimpan di folder `tmp/` workspace dan dimuat sekali saat server
mulai. Setelah bobot tersedia secara lokal, analisis teks tidak memerlukan unduhan
model lagi. `CAFESTOCK_INDOBERT_PATH` dapat dipakai untuk menunjuk checkpoint lain.
Checkpoint tidak diunggah ke GitHub. Pada CPU, pembuatan checkpoint memerlukan
sekitar 30 menit dan koneksi internet untuk mengambil base model.

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
6. Coba teks pembahasan menu untuk melihat hasil inferensi IndoBERT empat kelas.

Grafik garis pada alasan pembelian memproyeksikan stok per hari tanpa pembelian
dan setelah rencana pesanan diterima, dilengkapi garis titik pemesanan dan target
stok dari kebijakan terpilih. Rincian menunjukkan ramalan kebutuhan harian, faktor
keamanan, waktu tunggu pemasok, serta pembulatan ke minimum dan kelipatan kemasan.
Grafik ini menerangkan keputusan persediaan; grafik tren pasar ada di bagian
analisis pasar dan tidak menentukan jumlah beli secara langsung.

Jumlah pembelian berasal dari kebijakan stok yang dipilih pada validation. Skor
risiko berasal dari kondisi kebijakan historis pada tanggal yang ditampilkan;
skor tersebut bukan risiko terkalibrasi pada stok hasil simulasi kebijakan baru.
Data awal yang belum memiliki prediksi sentimen historis dinyatakan belum tersedia.

### Dua jalur sentimen

Form analisis teks menggunakan IndoBERT fine-tuned empat kelas. Sementara itu,
garis sentimen historis dalam grafik dan fitur yang dipakai model risiko berasal
dari prediksi SVM kronologis. Jalur historis dipertahankan agar hasil evaluasi
risiko tetap dapat direproduksi. Hasil challenge IndoBERT pada data sintetis
adalah akurasi 54,7%; recall positif 7,6%, sehingga hasilnya belum boleh dianggap
sebagai kinerja pada ulasan konsumen nyata. Lihat [rincian per kelas](../reports/indobert_experiment/report.md).

## Analisis tren pasar di dashboard

Bagian **Analisis tren, sentimen, penjualan & stok** berada sebelum rekomendasi pembelian. Pilih kategori
kopi, teh, roti/pastry atau minuman cokelat dan periode 4, 12, 26 atau 52 observasi
mingguan. Grafik indeks 0–100 dilengkapi perubahan mingguan, perbandingan rata-rata
empat minggu dengan empat minggu sebelumnya, serta pemetaan menu dan bahan melalui resep.
Tabel mingguan dan perbandingan model operasional vs operasional + tren dapat dibuka.

Sumbernya adalah seri simulasi pasar Semarang dalam `market_trends.csv`, bukan
pengukuran pasar nyata per cabang. Hanya baris kota Semarang yang tersedia sebelum
waktu keputusan dipakai. Perubahan dinyatakan sebagai poin indeks, bukan perubahan
volume penjualan. Periode grafik mengubah jumlah observasi yang ditampilkan;
ringkasan empat mingguan selalu memakai delapan observasi terbaru yang tersedia.
Endpoint: `/api/trends?branch=1&weeks=12`.

### Membandingkan tren, sentimen, penjualan, dan stok

Grafik menampilkan empat garis yang dapat dipilih melalui checkbox:

- **Tren pasar:** indeks kategori pada tanggal pengamatan, sinyal kota Semarang.
- **Sentimen historis (SVM):** rata-rata prediksi penyebutan menu di kota dan wilayah cabang
  dari batch terakhir yang sudah tersedia sebelum pengamatan. Pembaruan bulanan
  digambar bertangga; batch yang belum tersedia menjadi celah, bukan skor netral.
- **Penjualan 7 hari:** jumlah unit menu kategori yang terpenuhi pada cabang
  terpilih selama tujuh hari sebelum tanggal grafik. Jendela tidak lengkap kosong.
- **Nilai stok:** stok akhir hari sebelumnya × biaya satuan bahan kategori,
  dalam IDR. Ini stok historis dengan kebijakan yang sama dengan data penjualan,
  bukan snapshot hasil optimasi. Setiap bahan dihitung sekali per kategori;
  bahan bersama menyebabkan nilai antar kategori tidak boleh dijumlahkan.

Mode default menormalkan setiap seri berdasarkan minimum–maksimum periode ke
0–100 agar bentuk gerakan terlihat. Seri konstan digambar di 50; skala ini tidak
menyatakan besaran atau satuan yang sama. Pilihan **Nilai asli per seri** membuat
panel dengan sumbu masing-masing. Nilai asli juga tersedia di tabel mingguan.

Tabel hubungan menghitung Pearson r dari **perubahan mingguan**, hanya pada
pasangan lengkap yang berurutan, minimal enam pasangan dengan variasi cukup.
r ≥ 0,3 diberi label cenderung sejalan; r ≤ −0,3 berlawanan; selain itu lemah.
Konstanta, data hilang, atau jendela terlalu pendek tidak diberi koefisien.
Hubungan ini deskriptif; tidak menyatakan sebab-akibat atau signifikansi statistik.
Pengulangan batch bulanan bukan sampel sentimen baru yang independen.

## Memperbarui artefak model

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

## Navigasi dan keterbacaan

- **Analisis pasar:** grafik empat seri, ringkasan hubungan, serta bahan prioritas.
- **Pembelian:** rencana lengkap dan filter **Perlu dibeli saja**.
- **Evaluasi & sentimen:** perbandingan kebijakan dan form analisis teks.

Cabang dan filter tersimpan pada URL sehingga tautan dapat dibuka kembali pada
kondisi yang sama. Di ponsel, navigasi berada di atas dan daftar pembelian
menampilkan tiap bahan beserta semua jumlahnya. Tombol **Coba muat kembali**
tersedia jika data gagal diambil.

[Laporan audit UI/UX](../reports/ui_readability_review.md) memuat bukti, arah visual,
serta perbandingan sebelum dan sesudah.
