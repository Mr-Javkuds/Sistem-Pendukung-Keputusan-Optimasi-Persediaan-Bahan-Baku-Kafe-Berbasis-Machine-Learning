# Dataset baru: ketertarikan publik terhadap menu

Tanggal: 8 November 2026. Identitas eksperimen: `laya_menu_interest_v1`.

[Notebook Kaggle privat](https://www.kaggle.com/code/yasinmuhammadyusuf/cafestock-laya-menu-interest-forecast)

Notebook versi 1 sudah selesai dijalankan. Hasil model ketertarikan: accuracy
**86,19%** dan macro-F1 **0,8601** pada 478 teks sintetis test. Delapan sanity check
aturan sesuai; ini bukan benchmark independen. [Laporan hasil dan audit](../reports/menu_interest_v1/report.md).

## Tujuan label

Label menilai arah ketertarikan mencoba menu target. Penilaian rasa, kualitas,
dan opini pribadi tidak otomatis menyatakan ketertarikan. Label ini berbeda
dari review produk serta eksperimen sentimen produk sebelumnya.

| Label | Arti | Contoh |
|---|---|---|
| positive | Tertarik atau ingin mencoba/memesan | Kelihatan enak, aku ingin coba! |
| negative | Secara eksplisit menolak atau tidak tertarik mencoba/memesan | Enak, tapi aku tidak tertarik mencoba. |
| neutral | Arah ketertarikan tidak jelas | Rasanya enak. / Rasanya mengecewakan. / Toppingnya apa? |
| mixed | Tertarik sekaligus ragu, enggan atau menolak | Pengin coba, tetapi masih ragu karena harganya. |

"Terlalu manis untuk seleraku" tetap neutral bila tidak menyatakan arah minat.
"Terlalu manis jadi aku tidak mau mencoba" menjadi negative. Pujian dan kritik
rasa sekaligus tidak otomatis mixed. Ketertarikan bukan transaksi atau bukti
niat membeli yang terverifikasi.

## Data yang tersedia

Data ada di `datasets/menu_interest_v1/`, dengan ZIP distribusi
`notebooks/laya_menu_interest_data.zip`. Seluruh postingan dan komentar bersifat
**sintetis**. Tidak ada scraping Instagram, identitas akun atau lokasi komentar
nyata. Label dibuat berdasarkan aturan/ungkapan penulis; belum anotasi manusia.

| Artefak | Jumlah / isi |
|---|---|
| posts.csv | 3.100 postingan; menu, caption, tag lokasi, publikasi, pengumpulan |
| comments.csv | 33.968 event komentar; teks, konteks, label ketertarikan dan metadata |
| train.csv | 1.275 teks eligible, setelah deduplikasi |
| validation.csv | 476 teks eligible |
| test.csv | 478 teks eligible |
| products.csv, recipes.csv, recipe_ingredients.csv | Pemetaan menu ke resep dan bahan proyek |
| branches.csv, ingredients.csv | Cabang dan satuan bahan |
| label_policy.txt | Pedoman anotasi lengkap |
| instructions.txt | Instruksi ringkas model |
| dataset_manifest.json | Jumlah, provenance, waktu, aturan sumber |

Jumlah event mentah bukan jumlah ungkapan unik atau sampel independen. Caption
dan komentar memakai keluarga pola sintetis yang diulang. Deduplikasi untuk NLP
tidak menghapus event mentah yang diperlukan untuk audit sumber. `eligible`
berarti teks pertama yang lolos deduplikasi; hanya partisi train yang diberikan
untuk pembaruan bobot. Baris forecast tidak masuk pelatihan teks.

Input Laya berupa JSON di field `review`:

```json
{
  "target_product": "Es Matcha Latte",
  "parent_caption": "Konteks unggahan menu",
  "comment_text": "Ingin mencoba, tapi masih ragu."
}
```

ID, waktu, family_id, wilayah dan label tidak diberikan sebagai fitur teks.
Caption promosi hanyalah konteks; pujian pada caption tidak disalin menjadi
ketertarikan penulis komentar.

## Urutan waktu

| Tahap | Waktu ketersediaan data |
|---|---|
| NLP train | collected_at sebelum 1 Februari 2026 |
| NLP validation | Februari 2026 |
| NLP test | Maret 2026 |
| Checkpoint beku dianggap tersedia | 1 April 2026 |
| Awal evaluasi ramalan kebutuhan | 7 April 2026 pukul 05.00 WIB |

Komentar Senin–Minggu dikumpulkan Senin berikutnya pukul 07.00 WIB. Satu postingan
tetap dalam satu partisi; keluarga ungkapan train/validation/test juga dipisah.
Teks duplikat hanya mengambil kemunculan pertama untuk NLP. Postingan terminal
yang belum terkumpul pada akhir periode mempunyai split pending.

Inferensi checkpoint beku pada data sebelum April hanya dipakai evaluasi NLP.
Fitur peramalan yang dinilai dimulai setelah tanggal ketersediaan checkpoint.
Agregasi pada setiap keputusan hanya memakai collected_at < decision_at.
Parameter/threshold tidak dipilih dari test. Pelatihan terjadi saat eksperimen
dijalankan, sedangkan batas waktu tersebut adalah protokol rekonstruksi simulasi.

## Lokasi dan pengendalian sumber

- Wilayah berasal dari tag lokasi postingan sintetis: kota Semarang dan tiga
  wilayah cabang. Tag tidak menyatakan lokasi penulis komentar.
- Lokasi pemberi komentar tetap kosong. Tag postingan unknown tidak ditebak dan
  dikeluarkan dari agregat wilayah.
- Maksimal lima komentar pertama secara waktu per postingan dipakai pada skor.
- Skor tiap postingan adalah rata-rata label terpilih: positive +1, negative -1,
  neutral/mixed 0. Setiap postingan kemudian mendapat bobot yang sama, satu unit.
- Jumlah postingan, komentar mentah, dan komentar yang lolos cap dicatat terpisah.
  Posting berisi 40 komentar tidak memperoleh delapan kali bobot posting 5 komentar.
- Ini membatasi dominasi satu postingan, bukan pendeteksi bot atau akun terkoordinasi.
- Sinyal kota dan wilayah cabang digunakan sebagai konteks simulasi; hubungan dengan
  permintaan setempat adalah asumsi yang diuji.

## Peramalan dan tiga skenario

Notebook melatih Laya dari multilingual dasar dengan task `menu_interest`, lalu
memakai **prediksi Laya**, bukan label generator, sebagai fitur C/D.

| Versi RF Regressor | Fitur |
|---|---|
| A | Cabang, bahan, konsumsi rata-rata 14 hari, minggu dalam tahun |
| B | A + indeks tren kategori |
| C | A + skor ketertarikan prediksi Laya, ketersediaan, jumlah postingan/komentar terpilih |
| D | A + tren + kelompok fitur ketertarikan |

Model: 80 pohon, max_depth 12, min_samples_leaf 8, seed 42, sama untuk seluruh
versi. Encoder di-fit pada train. Ini ablation kelompok fitur; C/D belum
mengisolasi polaritas dari ketersediaan dan volume sumber.
Indeks tren sintetis diasumsikan sudah teramati pada waktu keputusan.

Simulator membentuk permintaan menu lalu mengalikannya dengan resep untuk target
rata-rata kebutuhan harian bahan selama tujuh hari. Pembanding historis memakai
dua minggu sebelumnya. Setiap skenario menggunakan 900 baris bahan–cabang–minggu:
630 train, 120 validation, 150 test. Target tujuh hari tidak melintasi partisi.
Ada 30 tanggal keputusan, dengan lima tanggal test; sampel waktu masih kecil.

Tiga skenario memakai koefisien ketertarikan referensi **0,8 (kuat), 0,15 (lemah),
dan 0 (nol)**. Sinyal referensi hanya mendefinisikan hipotesis simulator. Noise,
tren, resep dan waktu keputusan identik antar-skenario; riwayat konsumsi dihitung
ulang dari permintaan masing-masing skenario. Fitur model tetap memakai Laya.

Tidak ada kewajiban D menang. Perbedaan pada skenario nol dapat muncul karena
kebetulan sampel atau overfitting. Evaluasi utama MAE per bahan; RMSE juga
disimpan. Rasio MAE terhadap A boleh dirata-ratakan karena tidak bersatuan;
MAE gram, mililiter dan piece tidak dijumlahkan langsung.

## Batas klaim dan output

Eksperimen menguji kontribusi tren dan ketertarikan terhadap ramalan kebutuhan
dalam simulasi. Tidak membuktikan ketertarikan menjadi pembelian, lokasi
pemberi komentar, keuntungan, penghematan biaya atau pengurangan limbah nyata.
Tidak ada replay pengadaan dalam eksperimen ini.

Notebook menulis checkpoint Laya baru, test NLP, challenge aturan, audit bobot
postingan/waktu, fitur peramalan, prediksi A–D, MAE/RMSE per bahan, dan manifest
hash. Model disimpan dalam output Kaggle `laya_menu_interest_v1/model` dan arsip
`laya_menu_interest_v1.zip`. Model terdahulu tetap tersimpan. Form dashboard
menyediakan model ketertarikan v2 sebagai Laya Tren Sentimen; hasil peramalan
di eksperimen ini tetap berasal dari model v1.

Generator lokal:

```powershell
../.venv/Scripts/python.exe prepare_menu_interest.py
```

Generator menulis ulang ZIP dan notebook eksperimen ini. CSV yang sudah diekstrak
di datasets adalah snapshot; ganti snapshot hanya setelah memeriksa perubahan
generator. Untuk klaim di luar simulasi, diperlukan data komentar berkonteks
yang dianotasi manusia dan evaluasi pada periode baru.
