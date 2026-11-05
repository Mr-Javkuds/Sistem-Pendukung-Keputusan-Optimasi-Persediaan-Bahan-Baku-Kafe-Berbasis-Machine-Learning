# Analisis kesalahan model test

Analisis ini dilakukan setelah model/threshold dibekukan. Tidak digunakan untuk memilih fitur atau parameter ulang.

## Sentimen

SVM dan Naive Bayes tidak membuat kesalahan pada teks eligible test sintetis. Hasil sempurna konsisten dengan template frasa dan label generator yang sederhana; evaluasi ini belum menguji bahasa informal, ironi, multi-menu, atau Instagram nyata.

## Risiko per bahan

| Bahan | N test | False negative | False positive | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| Biji kopi | 141 | 0 | 66 | 0.5319 | 1.0000 |
| Susu | 141 | 0 | 59 | 0.5816 | 1.0000 |
| Bubuk matcha | 141 | 18 | 16 | 0.7576 | 0.7353 |
| Daun teh | 141 | 0 | 27 | 0.8085 | 1.0000 |
| Bubuk cokelat | 141 | 0 | 30 | 0.7872 | 1.0000 |
| Pemanis | 141 | 0 | 66 | 0.5319 | 1.0000 |
| Es batu | 141 | 0 | 39 | 0.7234 | 1.0000 |
| Adonan croissant | 141 | 0 | 66 | 0.5319 | 1.0000 |
| Porsi adonan muffin | 141 | 0 | 41 | 0.7092 | 1.0000 |
| Air tersaring | 141 | 32 | 17 | 0.6964 | 0.5493 |

## Contoh kasus yang terlewat (false negative)

| Waktu keputusan | Cabang | Bahan | Stok | Pesanan berjalan | Skor risiko |
|---|---|---|---:|---:|---:|
| 2026-09-11T05:00:00+07:00 | 1 | Air tersaring | 27130.0 | 0.0 | 0.243 |
| 2026-09-12T05:00:00+07:00 | 2 | Bubuk matcha | 190.0 | 0.0 | 0.244 |
| 2026-09-15T05:00:00+07:00 | 2 | Bubuk matcha | 130.0 | 0.0 | 0.249 |
| 2026-09-15T05:00:00+07:00 | 3 | Air tersaring | 27900.0 | 0.0 | 0.246 |
| 2026-09-16T05:00:00+07:00 | 1 | Air tersaring | 21440.0 | 0.0 | 0.235 |

## Ketergantungan model dan implikasi

Lima fitur dengan penurunan AP terbesar saat diacak: on_hand, shelf_life_days, branch_id, package_size, market_interest_latest.
Kasus false negative merupakan kejadian stockout yang labelnya baru diketahui setelah keputusan. Stok saat ini saja tidak menjamin kecukupan bahan selama tujuh hari; pesanan masuk, konsumsi, bahan lain dalam resep dan kebijakan historis ikut menentukan outcome.
False positive dapat menghasilkan prioritas berlebih; skor risiko tidak langsung diubah menjadi jumlah beli. Jumlah beli ditentukan terpisah oleh forecast dan kebijakan stok yang diuji ulang.
Importance mengukur ketergantungan prediksi, bukan penyebab stockout. Kontribusi sentimen harus dibaca bersama ablation D vs E (volume tetap tersedia).

[Semua kasus salah](../prepared/07_modeling/risk_error_cases.csv) memuat fitur saat keputusan dan label aktual untuk audit.
