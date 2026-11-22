# Model Laya: review produk, sentimen produk, dan ketertarikan menu

Rancangan aktif untuk sinyal pasar sekarang menggunakan **ketertarikan terhadap
menu**, dengan dataset dan notebook baru: [pedoman serta dataset ketertarikan](dataset_ketertarikan_menu.md).
Eksperimen sentimen produk di bawah tetap disimpan sebagai eksperimen terpisah;
hasilnya bukan evaluasi model ketertarikan yang baru.

Tanggal pemisahan: 8 November 2026.

| Model | Tugas | Lokasi |
|---|---|---|
| `laya_product_reviews_v1` | Penilaian pengalaman konsumsi/review produk | `local/laya_product_reviews_v1` |
| `laya_public_product_trends_v1` | Sikap publik terhadap produk target, berdasarkan komentar dan konteks unggahan | `local/laya_public_product_trends_v1/model` |
| `laya_menu_interest_v1` | Arah ketertarikan mencoba menu target; evaluasi waktu dan skenario peramalan | Output notebook Kaggle ketertarikan |
| `laya_menu_interest_v2` | Fine-tuning lanjutan ketertarikan; kandidat warm8, belum konsisten >95% antar-set | `local/laya_menu_interest_v2/model` |

Model v2 telah diunduh dan ketujuh file checkpoint diverifikasi SHA-256.
Accuracy validation 94,54%, test lama 84,73%, konfirmasi baru 98,85%.
[Laporan evaluasi v2](../reports/menu_interest_v2/report.md). Model ini tersedia sebagai pilihan **Laya Tren Sentimen** pada form dashboard.
Seri historis dan pipeline peramalan tetap memakai artefak evaluasi sebelumnya.

## Model review yang dipertahankan

Checkpoint yang sebelumnya dipakai aplikasi di `local/laya_cafestock_finetuned`
disalin ke `local/laya_product_reviews_v1`. Ketujuh file diverifikasi SHA-256;
hasilnya ada di `preservation_manifest.json` pada direktori salinan. Notebook
review lama `notebooks/laya_kaggle_finetuning.ipynb` tetap tersedia.

Model lama memakai label review, termasuk keluhan tingkat manis sebagai negative.
Jangan menyamakan aturan ini dengan aturan model publik yang baru. Dashboard
masih memakai konfigurasi model lama; pemisahan ini tidak mengganti hasil historis
SVM atau model peramalan persediaan.

## Model publik baru

[Notebook Kaggle privat](https://www.kaggle.com/code/yasinmuhammadyusuf/cafestock-laya-public-product-sentiment),
versi 2 telah menyelesaikan training dan evaluasi.

Sumber lokal: `notebooks/laya_public_product_trends_kaggle.ipynb`.
Generator: `prepare_laya_public_trends.py`. Input terkemas di
`notebooks/laya_public_product_trends_data.zip` serta tertanam dalam notebook.

Training dimulai dari checkpoint Laya multilingual dasar, bukan dari checkpoint
review produk. Input model berupa JSON di field `review` dengan:

```json
{
  "target_product": "Es Matcha",
  "parent_caption": "Konteks unggahan yang membahas menu ini",
  "comment_text": "Kelihatannya enak, pengin coba!"
}
```

`parent_caption` hanya konteks; sentimen promosi pada caption tidak boleh dianggap
sebagai opini penulis komentar. Opini tentang produk lain tidak otomatis menjadi
opini terhadap produk target.

## Pedoman sentimen produk pada eksperimen terdahulu

| Label | Makna | Contoh |
|---|---|---|
| positive | Pujian, antusiasme, ketertarikan atau ingin mencoba target | Kelihatannya enak, pengin coba! |
| negative | Kritik kualitas atau penolakan eksplisit terhadap target | Cuma menang tampilan, rasanya mengecewakan. |
| neutral | Pertanyaan, fakta, opini belum terbentuk atau preferensi pribadi tanpa penilaian kualitas | Itu topping apa? / Terlalu manis untuk seleraku. |
| mixed | Pujian dan kritik kualitas yang sama-sama jelas | Aromanya harum, tapi rasanya gosong. |

Sesuai keputusan pengguna, preferensi pribadi saja masuk neutral. Pujian disertai
preferensi pribadi saja tetap positive; mixed memerlukan kritik kualitas yang
eksplisit. Ungkapan "untuk seleraku" tidak menetralkan keluhan bahan basi/gosong.

## Data dan evaluasi

- Train: 1.944 baris; validation: 198; test: 198.
- Data awal sintetis yang ditulis untuk eksperimen, bukan komentar Instagram nyata.
- Keluarga ungkapan dan produk dipisahkan antar-split; fingerprint komentar diperiksa.
- Pembagian berdasarkan kelompok, bukan kronologis. Untuk pemakaian pada keputusan
  stok historis, perlu checkpoint pra-periode atau training expanding-window.
- Ada 12 challenge diagnostik terpisah untuk ketertarikan sebelum mencoba,
  pertanyaan, preferensi, negasi, pujian/cacat dan konteks unggahan.
  Ini pemeriksaan aturan, bukan benchmark independen: contoh preferensi mirip
  contoh pada train dan pedoman label.
- Validation dipakai CLI untuk evaluasi; test baru dihitung setelah training.
- Metrik: accuracy, macro-F1, precision/recall per kelas, confusion matrix dan kasus salah.
- Instruksi model dipadatkan agar seluruh aturan muat dalam batas head 128 token;
  pedoman anotasi Bahasa Indonesia yang lengkap tetap disertakan dalam arsip.
- Skor test sintetis belum membuktikan kinerja pada opini publik nyata. Data nyata
  perlu anotasi manusia menggunakan pedoman baru sebelum klaim generalisasi.

Hasil test versi 2: accuracy **85,86%** (170/198), macro-F1 **0,8602**.
Komentar ingin mencoba, pertanyaan topping, dan preferensi pribadi pada challenge
sudah diprediksi sesuai pedoman. Pujian yang disertai preferensi pribadi masih
kadang diprediksi mixed. [Laporan evaluasi dan batasnya](../reports/laya_public_product_trends/report.md).

## Output training

Notebook menulis `laya_public_product_trends_v1.zip`, berisi model, pedoman label,
manifest/hash, metrik test, prediksi test, kesalahan dan prediksi challenge.
Arsip sudah diunduh ke `local/laya_public_product_trends_v1.zip` dan diekstrak
ke `local/laya_public_product_trends_v1/`. Ketujuh file checkpoint sudah
diverifikasi SHA-256 terhadap manifest Kaggle versi 2.

Demonstrasi agregasi menampilkan volume komentar, skor (positive-negative)/total,
proporsi mixed dan neutral. Ini sinyal opini produk; bukan ukuran popularitas
representatif, bukti niat membeli, atau ramalan jumlah stok.
