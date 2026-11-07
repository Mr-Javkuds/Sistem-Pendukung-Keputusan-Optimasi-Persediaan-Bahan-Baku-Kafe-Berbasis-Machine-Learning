# Uji tantangan sentimen — 2.000 input

**Label acuan ditetapkan sebelum prediksi; model produksi tidak dilatih ulang atau diganti.**

400 skenario makna × 5 variasi bahasa menghasilkan 2.000 teks unik, juga unik setelah NFKC/casefold/normalisasi spasi. Masing-masing kelas berisi 500 input. Tidak ada teks yang sama persis dengan train setelah normalisasi.
Ini uji terkontrol buatan penulis, bukan 2.000 ulasan manusia independen. Label mengikuti rubric positif/negatif/netral/campuran rasa dan nilai; belum ditinjau anotator independen.

Akurasi challenge: **40.25%**. Macro F1: **0.3621**. Salah: **1,195 / 2.000**.

| Kelas acuan | Precision | Recall | F1 | Jumlah |
|---|---:|---:|---:|---:|
| positive | 0.3807 | 0.3000 | 0.3356 | 500 |
| negative | 0.4658 | 0.2720 | 0.3434 | 500 |
| neutral | 0.4533 | 0.9020 | 0.6033 | 500 |
| mixed | 0.2132 | 0.1360 | 0.1661 | 500 |

## Matriks kebingungan

Baris = acuan; kolom = prediksi.

| Acuan / prediksi | positive | negative | neutral | mixed |
|---|---:|---:|---:|---:|
| positive | 150 | 50 | 147 | 153 |
| negative | 19 | 136 | 247 | 98 |
| neutral | 46 | 3 | 451 | 0 |
| mixed | 179 | 103 | 150 | 68 |

## Variasi bahasa

| Variasi | Jumlah | Akurasi |
|---|---:|---:|
| casing_punctuation | 400 | 40.75% |
| formal | 400 | 40.75% |
| informal | 400 | 34.00% |
| social_context | 400 | 43.50% |
| typo | 400 | 42.25% |

## Pola makna

| Pola | Jumlah | Akurasi |
|---|---:|---:|
| direct_opinion | 490 | 30.41% |
| factual_no_opinion | 500 | 90.20% |
| negation_or_scope | 510 | 26.86% |
| taste_negative_value_positive | 250 | 13.60% |
| taste_positive_value_negative | 250 | 13.60% |

## Endpoint aplikasi

```json
{
  "executed": true,
  "requests": 2000,
  "successful": 2000,
  "errors": 0,
  "matches_frozen_batch_model": 2000,
  "accuracy": 0.4025,
  "latency_median_ms": 20.12995001859963,
  "latency_p95_ms": 36.913560010725625
}
```

## Contoh kesalahan (variasi formal)

| Teks | Acuan | Prediksi |
|---|---|---|
| Untuk es latte, rasanya lezat dan membuat saya ingin pesan lagi. Selain itu, harganya terjangkau dan pantas untuk kualitas ini. | positive | mixed |
| Untuk cokelat panas, rasanya lezat dan membuat saya ingin pesan lagi. Selain itu, harganya tidak mahal dan saya puas dengan nilainya. | positive | mixed |
| Untuk teh chai, rasanya lezat dan membuat saya ingin pesan lagi. Selain itu, menurut saya ini layak dibeli lagi dengan harga tersebut. | positive | neutral |
| Untuk kopi seduh, rasanya lezat dan membuat saya ingin pesan lagi. Selain itu, biayanya ramah di kantong untuk porsi yang saya dapat. | positive | mixed |
| Untuk es latte, rasanya tidak enak dan saya tidak mau pesan lagi. Selain itu, harganya kelewat mahal untuk porsi sekecil ini. | negative | mixed |
| Untuk matcha latte, rasanya tidak enak dan saya tidak mau pesan lagi. Selain itu, saya merasa rugi karena porsinya tidak sepadan dengan harga. | negative | positive |
| Untuk cokelat panas, rasanya tidak enak dan saya tidak mau pesan lagi. Selain itu, harga seperti ini tidak masuk akal bagi saya. | negative | mixed |
| Untuk teh chai, rasanya tidak enak dan saya tidak mau pesan lagi. Selain itu, biayanya terlalu tinggi sehingga tidak layak dibeli lagi. | negative | positive |
| Untuk teh chai, tercantum dalam daftar minuman hari ini; nama menu dan ukurannya akan saya masukkan ke tabel. | neutral | positive |
| Untuk kopi seduh, tercantum dalam daftar minuman hari ini; catatan tersebut berisi nama minuman, jumlah, dan ukuran gelas. | neutral | positive |
| Untuk kopi seduh, namanya tertulis di papan menu dekat kasir; informasi bahan akan saya baca sebelum memutuskan pesanan. | neutral | negative |
| Untuk matcha latte, namanya tertulis di papan menu dekat kasir; catatan tersebut berisi nama minuman, jumlah, dan ukuran gelas. | neutral | positive |
| Matcha latte ini rasanya lezat dan membuat saya ingin pesan lagi, tetapi saya merasa rugi karena porsinya tidak sepadan dengan harga. | mixed | positive |
| Cokelat panas ini rasanya lezat dan membuat saya ingin pesan lagi, tetapi harga seperti ini tidak masuk akal bagi saya. | mixed | neutral |
| Teh chai ini rasanya lezat dan membuat saya ingin pesan lagi, tetapi biayanya terlalu tinggi sehingga tidak layak dibeli lagi. | mixed | positive |
| Kopi seduh ini rasanya lezat dan membuat saya ingin pesan lagi, tetapi porsinya mengecewakan untuk uang yang sudah saya keluarkan. | mixed | positive |

## Diagnosis dan batas

Generator latih hanya mempunyai empat pola rasa positif, empat negatif, empat netral, dan tiga kalimat nilai/harga. Mixed latih selalu rasa positif + harga negatif. Arah sebaliknya tidak diajarkan. Test lama berasal dari generator yang sama, sehingga skor 1,0 tidak mengukur generalisasi bahasa bebas.
Rata-rata n-gram yang tidak ada dalam kosakata model: 69.42%. Seluruh lima variasi benar pada 112 dari 400 skenario. Angka ini bukan interval kepercayaan atas populasi ulasan nyata.
Negasi, bahasa informal, typo, fakta netral dan mixed arah terbalik perlu tercakup pada data anotasi yang lebih beragam. Challenge ini harus tetap terpisah dari train/tuning; jika dipakai merancang perbaikan, perlukan test baru yang belum dilihat untuk klaim akurasi berikutnya.
Belum ada klaim bahwa sarana demo ini siap untuk ulasan nyata. Tidak ada perubahan otomatis pada classifier, grafik, fitur stok, atau model produksi.

[Seluruh input dan acuan](cases_2000.csv) · [Prediksi lengkap](predictions_2000.csv) · [Semua kesalahan](errors.csv) · [Hasil JSON](results.json) · [Rubrik dan hash](manifest.json)
