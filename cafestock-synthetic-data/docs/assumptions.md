# Asumsi, provenance dan batas eksperimen — Semarang

## Skenario

CafeStock Coffee adalah perusahaan fiktif; cabang Semarang Tengah, Semarang
Selatan, dan Banyumanik bukan lokasi bisnis yang diverifikasi. Region Semarang
adalah konteks pasar; nama wilayah bukan klaim adanya akun/kafe nyata di alamat
tertentu. Periode simulasi 2025-11-04 s.d. 2026-11-03, zona Asia/Jakarta, IDR.
Semua output adalah sintetis; input sumber tetap terpisah dan dihash.

## Penjualan dan harga

CSV transaksi eksternal Januari–Juni 2023 memberi pola jam, weekday, popularitas
proxy jenis produk dan kuantitas. Cabang Semarang memakai proxy eksplisit
Lower Manhattan/Hell's Kitchen/Astoria hanya untuk variasi statistik. Tidak ada
klaim bahwa transaksi sumber terjadi di Semarang atau pelanggan sama.
Jumlah transaksi harian Poisson, skala konfigurasi default 90/cabang, dikalikan
weekday per eksposur hari dan faktor musim amplitudo 10%. Produk dipilih menurut
popularitas proxy dan bobot tren dengan lag minimal 7 hari.

Harga IDR diasumsikan per produk: Kopi Seduh 18.000; Espresso 18.000; Latte Panas
25.000; Es Latte 28.000; Es Matcha Latte 30.000; Teh Chai 18.000; Teh Hijau 16.000;
Cokelat Panas 25.000; Butter Croissant 18.000; Blueberry Muffin 20.000. Variasi
ukuran/porsi ditiru dengan tambahan 0/2.000/4.000, peluang 70/20/10%. Ini bukan
harga pasar yang diobservasi, bukan kurs konversi, dan bukan label optimal.
Source USD prices dilaporkan terpisah dan tidak dibandingkan sebagai satu mata uang.

## Instagram sintetis

Default jumlah postingan harian Poisson dengan mean 18, independen dari transaksi.
Tiap postingan membahas satu menu, dalam bahasa Indonesia, dengan satu wilayah:
Semarang kota 35%, Semarang Tengah 20%, Semarang Selatan 20%, Banyumanik 20%,
unknown 5%. Pembagian ini asumsi simulasi, bukan cakupan Instagram sesungguhnya.
Nama wilayah ditempatkan dalam teks sesuai skenario; bukan geotag terverifikasi.
Tidak ada nama akun, nama individu, akun pelanggan, ataupun URL Instagram nyata.
platform=instagram hanya menjelaskan bentuk data yang ditiru; provenance=synthetic.
source_post_key berawalan SIM-IG-SMG-. Tidak ada rating atau hubungan ke pembelian.

Label menu memiliki peluang positive 45%, neutral 20%, negative 20%, mixed 15%.
Teks dirakit dari frasa asli pendek dan variasi pembuka/penutup. Untuk positive,
negative dan neutral, aspek taste/value mempunyai label yang sama. Mixed memakai
aspek rasa positif dan nilai/harga negatif. Label berasal dari aturan generasi,
bukan rating, hasil model, maupun Yelp. Label netral dapat berisi pembahasan menu
tanpa penilaian. Sentimen tidak menggerakkan penjualan dalam generator; penelitian
boleh menemukan kontribusi prediktif yang kecil atau nol.

Template yang terbatas dapat menghasilkan pengulangan dan membuat tugas klasifikasi
terlalu mudah. Untuk ML, caption dinormalisasi NFKC/casefold/whitespace lalu dihash;
kemunculan eligible pertama menurut collected_at dipertahankan dan kemunculan
ulang/konflik label berikutnya dikeluarkan. Pending tetap tidak eligible. Tidak
ada pemindahan catatan antarwaktu. Postingan dan sinyal pasar mentah tetap utuh
untuk menjaga jejak event; kebijakan ini bukan pendeteksi konten bot. Lakukan
audit kemiripan template dan laporkan keterbatasan; jangan memakai
hasil ini untuk klaim performa NLP media sosial nyata. Komentar multi-menu dan
hubungan reply belum disimulasikan, walau junction menu_mentions mendukung
beberapa menu pada satu post. Engagement dan bot akun belum disimulasikan.

## Waktu koleksi dan agregasi

published_at berada di periode simulasi. collected_at adalah tanggal 1 bulan
berikutnya pukul 07:00 WIB. Ini asumsi jadwal pengambilan bulanan, bukan klaim
scraping sudah dijalankan. Postingan November 2026 dapat disimpan tetapi baru
tersedia 1 Desember; split=pending mengeluarkannya dari training/evaluasi saat ini.

Agregat menu_market_signals mengelompokkan region_id, product_id dan bulan publikasi.
Hanya lokasi diketahui yang masuk; tersedia ketika batch sudah dikumpulkan.
Sentimen = (jumlah positive - jumlah negative)/jumlah postingan; mixed/neutral
berskor 0. Jumlah postingan dan availability flag tetap disimpan: tidak ada data
bukan berarti sentimen netral atau permintaan nol. Volume adalah jumlah sampel
sintetis, bukan pangsa pasar.

Fitur keputusan mengambil bulan terbaru yang tersedia sebelum decision_at,
produk yang resepnya menggunakan bahan terkait, dan region kota plus region
cabang. Pembahasan wilayah cabang lain dan unknown tidak masuk. Postingan kota
dapat dipakai beberapa cabang: ini sinyal pasar bersama, bukan observasi penjualan
independen di setiap cabang. market/social timestamp metadata tidak menjadi fitur ML.

## Google Trends

geoMap.csv adalah geografi; multiTimeline.csv adalah deret matcha Jawa Tengah.
Keduanya tetap disimpan sebagai konteks sumber, bukan pengukuran menu Semarang
khusus. market_trends.csv adalah seri mingguan kategori Semarang yang sepenuhnya
disimulasikan: 52 + 16*sin(2*pi*(dayofyear/365.25+category/8)) + AR(1), rho .72,
innovation SD 4, clip [0,100], 10 minggu warm-up. Bobot pemilihan menu adalah
exp(.012*(indeks_lag-50)), dinormalisasi antarproduk. Tren mengubah komposisi menu,
bukan jumlah total transaksi harian. Permintaan mengikuti lag sekurangnya 7 hari.
Fitur menyertakan indeks terakhir dan lag 1 minggu, hanya yang sudah tersedia.
Karena hubungan tren diasumsikan, model yang berhasil hanya membuktikan pemulihan
pola simulasi, bukan kausalitas pasar nyata. Harga/volume/sentimen tidak dapat
ditafsirkan sebagai kondisi Instagram atau bisnis Semarang yang sebenarnya.

## Resep, biaya dan stok

Resep dan atribut pemasok adalah asumsi di src/generate_recipes.py: kopi 18 g,
susu latte 180–200 ml, matcha 5 g + 200 ml susu + 150 g es + 15 ml pemanis,
teh 3–4 g, cokelat 25 g + 220 ml susu, bakery satu porsi siap olah. Air dimodelkan
sebagai pembelian air tersaring dan es sebagai kantong pembelian. Tidak ada
konversi g ke ml; kuantitas mengikuti ingredients.unit.

Biaya dasar IDR: biji kopi 200/g, susu 20/ml, matcha 350/g, teh 100/g, cokelat
80/g, pemanis 25/ml, es 2/g, adonan croissant 5.500/piece, muffin 4.500/piece,
air .2/ml. Semua angka adalah asumsi engineering, bukan kutipan pemasok nyata.
Masa simpan, kemasan, MOQ dan lead time tercantum di ingredients/suppliers.

FEFO memilih lot terdekat kedaluwarsa. Stok awal prior menu rata-rata x transaksi
harian konfigurasi x 1,5 porsi, untuk 2 hari, dibulatkan kemasan. Lot expired menjadi
waste 01:00; discrepancy fisik bersimulasi peluang .8% per hari hingga 2% kemasan
dicatat 02:00; receipt 04:00; keputusan 05:00; penjualan mengikuti jam sumber
06:00–20:59. Lead time kalender pemasok 1 atau 3 hari, tanpa keterlambatan acak.
Tidak ada stok negatif; hanya fulfilled_qty yang mengonsumsi bahan. requested_qty
adalah permintaan laten. Kekurangan per bahan bisa mempunyai beberapa penyebab
untuk satu transaksi; jangan jumlahkan unfulfilled_product_qty lintas penyebab.
Pesanan di luar akhir periode tetap open dengan delivered_at NULL.

Aturan baseline: rata-rata konsumsi 14 hari selesai, warm-up memakai prior;
reorder bila on_hand + on_order < mean*(lead+1); target mean*min(lead+2,shelf_life).
Kebutuhan positif dibulatkan ke kemasan dan MOQ. Aturan dapat menghasilkan waste
dan belum optimal; sinyal Instagram tidak langsung mengubah jumlah baseline.

## Split dan evaluasi

Split nominal 70/15/15 kronologis, label windows train/validation yang menyentuh
split berikutnya dipurge. Risiko stockout 7 hari memakai label_observed=1 dan
split != purged; terminal incomplete labels NULL. Sentimen split menurut collected_at,
bukan published_at; pending tidak dipakai training/evaluasi. Fit preprocessing hanya
pada train. Sinyal sentimen risiko saat ini memakai label aturan sebagai referensi;
alur SVM operasional memerlukan prediksi historis out-of-fold sebelum agregasi.

Model riset train-only sudah dilatih pada tahap 07–10; laporan ada di
[modeling_report.md](../reports/modeling_report.md) dan
[optimization_report.md](../reports/optimization_report.md). Mengimitasi baseline_purchase_qty dengan
regresi bukan optimasi. Kebijakan pembelian baru perlu disimulasikan ulang dengan
permintaan laten yang sama dan metrik biaya/limbah/stockout yang didefinisikan.
