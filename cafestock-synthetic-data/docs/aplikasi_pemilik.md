# Aplikasi pemilik CafeStock

[README utama](../../README.md) · [Alur proyek](alur_project_ml.md)

Dashboard lokal menampilkan snapshot keputusan terakhir simulasi, bukan data
kafe langsung. Analisis teks menyediakan tiga pilihan: IndoBERT, Laya Sentimen Produk, dan Laya Tren Sentimen.

## Menjalankan

Dari folder `cafestock-synthetic-data`, pasang dependensi ML (sekali per environment).
Untuk opsi IndoBERT, pasang dependensi IndoBERT dan buat checkpoint lokal. Untuk
opsi Laya, pasang paket Laya dan siapkan checkpoint lokal sesuai tabel di bawah.
Ketiga pilihan berjalan lokal tanpa API key.

```powershell
../.venv/Scripts/python.exe -m pip install -r requirements-ml.txt
```

Siapkan IndoBERT jika ingin memakai model lokal:

```powershell
../.venv/Scripts/python.exe -m pip install -r requirements-indobert.txt
../.venv/Scripts/python.exe experiment_indobert.py
```

Siapkan Laya multilingual lokal:

```powershell
../.venv/Scripts/python.exe -m pip install -r requirements-laya.txt
```

Checkpoint yang dipakai dashboard:

| Pilihan | Task | Checkpoint default |
|---|---|---|
| IndoBERT | Sentimen teks produk | `../tmp/indobert-cafestock-fourclass` |
| Laya Sentimen Produk | Opini kualitas/pengalaman konsumsi | `local/laya_product_reviews_v1` |
| Laya Tren Sentimen | Ketertarikan mencoba menu, dengan konteks postingan | `local/laya_menu_interest_v2/model` |

Dua checkpoint Laya dimuat saat pertama kali dipilih lalu digunakan kembali.
Aplikasi memeriksa file checkpoint dan task; pilihan yang belum siap dinonaktifkan.
Tidak ada penggantian otomatis ke model multilingual dasar. Variabel lingkungan
`CAFESTOCK_LAYA_PRODUCT_PATH` dan `CAFESTOCK_LAYA_TREND_PATH` dapat menunjuk
checkpoint lain dengan task yang sesuai. `CAFESTOCK_LAYA_PATH` tetap menjadi
alias konfigurasi lama untuk model produk. Restart server setelah mengganti path.
Bobot lokal berada pada folder yang diabaikan Git.

Jalankan server setelah menyiapkan pilihan model yang ingin dipakai:

```powershell
../.venv/Scripts/python.exe owner_app.py
```

Checkpoint IndoBERT disimpan di folder `tmp/` workspace dan dimuat sekali saat
server mulai. Jika checkpoint tidak ada, aplikasi tetap berjalan tetapi opsi
IndoBERT dinonaktifkan. Setelah bobot tersedia secara lokal, analisis teks tidak
memerlukan unduhan model lagi. `CAFESTOCK_INDOBERT_PATH` dapat dipakai untuk
menunjuk checkpoint lain.
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
6. Pada **Analisis sentimen menu**, pilih salah satu dari tiga model.
   IndoBERT dan Laya Sentimen Produk menerima teks ulasan. Laya Tren Sentimen
   juga meminta produk/menu target serta caption atau konteks postingan.
   Hasilnya dibaca sebagai tertarik mencoba, tidak tertarik, arah minat belum
   jelas, atau tertarik tetapi ragu/menolak. Probabilitas yang ditampilkan adalah
   skor label model, bukan peluang pembelian konsumen.

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

### Tiga model form dan jalur historis

IndoBERT serta Laya Sentimen Produk menggunakan label opini positif, negatif,
netral, campuran. Laya Tren Sentimen menggunakan checkpoint ketertarikan v2
(warm8): pujian atau keluhan rasa saja dapat netral jika arah minat belum jelas.
Model tren membaca JSON produk target, konteks postingan dan komentar dengan
question `menu_interest`, sesuai format training.

Model v2 memiliki accuracy validation 94,54%, test lama 84,73%, dan konfirmasi
baru 98,85% pada data sintetis; kinerjanya belum konsisten >95% antar-set.
[Laporan lengkap](../reports/menu_interest_v2/report.md). Nama Laya Tren Sentimen
menunjukkan pembacaan ketertarikan publik, bukan peramalan tren atau jumlah stok.

Pilihan model pada form tidak mengganti seri sentimen historis SVM, model risiko,
atau hasil peramalan/pembelian yang telah dievaluasi. Grafik historis tetap
menggunakan prediksi SVM kronologis agar evaluasi lama dapat direproduksi.

API `/api/sentiment` menerima model `indobert`, `laya_product`, atau `laya_trend`.
Alias lama `laya` tetap mengarah ke model produk. Model tren wajib menyertakan
`target_product` (1–160 karakter), `parent_caption` (1–2000), dan `text` (1–4000).
Respons menyertakan `task=menu_interest` untuk model tren dan `product_sentiment`
untuk kedua model produk. Endpoint `/api/sentiment/options` memuat ketersediaannya.

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

Klik/ketuk titik atau garis pada grafik untuk melihat hari, tanggal, nilai asli,
dan satuannya. Pada mode gabungan 0–100, detail tetap menampilkan nilai asli.
Jika beberapa seri bertumpuk, nilai seri lain pada tanggal yang sama juga
ditampilkan. Klik di antara titik memilih pengamatan terdekat, bukan nilai
interpolasi. Tab dan Enter/Spasi dapat memilih titik; Escape atau tombol tutup
menyembunyikan detail. Di ponsel, detail ditampilkan di bawah grafik. Mengubah
filter atau periode menutup detail lama; celah data kosong tetap dipertahankan.

### Membandingkan tren, sentimen, penjualan, dan stok

Grafik menampilkan empat garis yang dapat dipilih melalui checkbox:

- **Tren pasar:** indeks kategori pada tanggal pengamatan, sinyal kota Semarang.
- **Sentimen historis (SVM):** rata-rata prediksi penyebutan menu di kota dan wilayah cabang
  dari batch terakhir yang sudah tersedia sebelum pengamatan. Pembaruan mingguan
  dihubungkan dengan garis diagonal antarobservasi; batch yang belum tersedia
  menjadi celah, bukan skor netral. Garis penghubung hanya panduan visual;
  pembaruan sentimen tetap mingguan.
- **Penjualan 7 hari:** jumlah unit menu kategori yang terpenuhi pada cabang
  terpilih selama tujuh hari sebelum tanggal grafik. Jendela tidak lengkap kosong.
- **Nilai stok:** stok akhir hari sebelumnya × biaya satuan bahan kategori,
  dalam IDR. Ini stok historis dengan kebijakan yang sama dengan data penjualan,
  bukan snapshot hasil optimasi. Setiap bahan dihitung sekali per kategori;
  bahan bersama menyebabkan nilai antar kategori tidak boleh dijumlahkan.

Mode default **Grafik terpisah dengan satuan asli** menampilkan setiap ukuran
pada panel dengan sumbu masing-masing. Mode gabungan menormalkan setiap garis
berdasarkan minimum–maksimum periode ke 0–100. Seri konstan digambar di 50;
skala gabungan tidak menyatakan besaran atau satuan yang sama. Nilai asli juga
tersedia di tabel mingguan. Ringkasan sentimen menyebutkan minggu asal dan jumlah
penyebutan menu; pembaruan tersedia setiap Senin pukul 07.00 WIB.

Tabel hubungan menghitung Pearson r dari **perubahan mingguan**, hanya pada
pasangan lengkap yang berurutan, minimal enam pasangan dengan variasi cukup.
r ≥ 0,3 diberi label cenderung sejalan; r ≤ −0,3 berlawanan; selain itu lemah.
Konstanta, data hilang, atau jendela terlalu pendek tidak diberi koefisien.
Hubungan ini deskriptif; tidak menyatakan sebab-akibat atau signifikansi statistik.
Pengulangan batch mingguan bukan sampel sentimen baru yang independen.

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
