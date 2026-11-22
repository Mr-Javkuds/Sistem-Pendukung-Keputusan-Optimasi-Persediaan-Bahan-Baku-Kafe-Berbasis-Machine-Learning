# Fine-tuning Laya di Kaggle

> Model dari eksperimen ini telah diarsipkan sebagai `local/laya_product_reviews_v1`
> untuk analisis review produk. Eksperimen baru komentar publik memakai notebook
> dan checkpoint terpisah: [pemisahan dua model Laya](laya_dua_model.md).

[Catatan presentasi](../reports/catatan_presentasi_laya.md) · [Alur proyek ML](alur_project_ml.md)

Panduan ini mendokumentasikan eksperimen fine-tuning **Laya multilingual** untuk
mengklasifikasikan teks pembahasan menu ke kelas positive, negative, neutral,
dan mixed. Model ini dipakai pada form analisis teks CafeStock. Model ini bukan
prediktor jumlah pembelian dan tidak menggantikan SVM kronologis pada fitur
sentimen historis yang digunakan pipeline risiko stok.

## Data dan split

Data contoh proyek bersifat **sintetis**, meniru pembahasan menu di Semarang;
bukan hasil scraping atau ulasan pelanggan nyata. Berkas awal memuat 3.361 baris
train, 664 validation, dan 620 test. Eksperimen ulang menambahkan 48 contoh
sintetis dengan variasi ungkapan ke train, sehingga berisi 3.409 baris sebelum
pembagian internal Laya. Laya menggunakan 3.069 baris untuk pembaruan parameter
dan 340 untuk kalibrasi internal. Validation digunakan untuk perbandingan
sebelum/sesudah training; test hanya dipakai untuk evaluasi akhir.

Kata **held-out** di laporan Kaggle berarti baris evaluasi dipisahkan dari baris
training/kalibrasi. Itu tidak berarti sumber bahasa atau pola kalimatnya
independen: semua split berasal dari generator sintetis yang sama.

## Menjalankan ulang di Kaggle

1. Unggah `notebooks/cafestock_laya_sentiment_data.zip` sebagai Kaggle Dataset.
2. Tambahkan dataset itu sebagai input notebook, aktifkan **GPU** dan **Internet**.
3. Buka `notebooks/laya_kaggle_finetuning.ipynb`, lalu jalankan semua sel.
4. Notebook melatih dari checkpoint dasar `multilingual`, mengevaluasi validation,
   kemudian menghitung classification report dan confusion matrix pada test.
5. Arsip model round 2 tersedia sebagai `laya_cafestock_round2.zip` pada output
   notebook Kaggle.

Untuk eksperimen terakhir, notebook Kaggle memakai GPU Tesla T4 dan `laya==0.4.27`:

| Pengaturan | Nilai |
|---|---:|
| Epoch | 2 |
| Micro-batch × gradient accumulation | 2 × 8 (effective batch 16) |
| Learning rate encoder / head | 1e-5 / 5e-5 |
| Objective | soft-ce |
| Label smoothing | 0.05 |
| Panjang teks maksimum | 256 token |
| Seed | 42 |

## Hasil eksperimen terakhir

- Validation: accuracy sebelum training **63,86%**, sesudah training **100%**
  pada 664 baris sintetis.
- Kaggle test: accuracy dan macro-F1 **100%** pada 620 baris sintetis.
- Uji tambahan lokal: **96/100** pada 100 kalimat variasi; label harapan pada
  set ini dibuat untuk pengujian, belum dianotasi manusia. Rinciannya ada pada
  [laporan evaluasi 100 kalimat](../reports/laya_100_sentence_eval.md).

Skor Kaggle yang sempurna tidak boleh dipresentasikan sebagai akurasi pada ulasan
pelanggan. Test terpisah berdasarkan baris, tetapi masih berbagi gaya dan pola
generator. Uji lokal 100 kalimat lebih beragam, tetapi juga bukan benchmark
berlabel manusia. Untuk klaim kinerja nyata, kumpulkan ulasan dengan izin,
anonimkan informasi pribadi, lalu minta anotasi manusia dan uji pada test yang
tidak dipakai memilih model.

## Checkpoint lokal

Model fine-tuned disimpan di `local/laya_cafestock_finetuned/`, folder ini
diabaikan Git. `owner_app.py` memakai checkpoint lokal jika tersedia dan
menampilkan label model tersebut pada hasil analisis. Jika checkpoint lokal
tidak ada, aplikasi kembali ke Laya multilingual dasar. Bobot model tidak
disimpan di GitHub.
