# Eksperimen IndoBERT untuk sentimen menu

- Base model: `indobenchmark/indobert-base-p1` (pretrained bahasa; classifier empat kelas di-fine-tune di data train proyek).
- Data latih: 3361 baris, split train proyek; challenge: 2.000 input beku.
- Runtime: cpu, 1937.8 detik, 2 epoch.
- Challenge yang sama seperti uji SVM sebelumnya; tidak dipakai saat fine-tuning.

> **Status:** IndoBERT ini sekarang dipakai oleh endpoint demo lokal. Akurasi total challenge lebih tinggi dari SVM, tetapi recall positif jatuh karena sebagian besar opini positif diprediksi campuran. Hasil ini tidak menunjukkan model siap untuk ulasan konsumen nyata.

| Model | Akurasi | Macro F1 |
|---|---:|---:|
| SVM TF-IDF (acuan) | 40.25% | 0.3621 |
| IndoBERT fine-tuned | 54.70% | 0.5084 |

## Per kelas dan perbandingan recall

| Kelas | SVM recall | IndoBERT recall | IndoBERT precision | IndoBERT F1 |
|---|---:|---:|---:|---:|
| positive | 30.0% | 7.6% | 1.0000 | 0.1413 |
| negative | 27.2% | 86.0% | 0.5614 | 0.6793 |
| neutral | 90.2% | 90.8% | 0.9558 | 0.9313 |
| mixed | 13.6% | 34.4% | 0.2386 | 0.2817 |

## Pola kegagalan

- Dari 500 input positif, IndoBERT hanya mengenali 38 sebagai positif; 441 diprediksi campuran.
- Pada kelas campuran, recall naik dari 13.6% (SVM) ke 34.4%, tetapi model masih melewatkan sebagian besar kasus.
- Challenge menguji dua arah campuran rasa/nilai, sedangkan generator data latih proyek hanya membentuk satu arah campuran. Ini kemungkinan besar membuat model berat sebelah.
- Variasi bahasa informal memperoleh akurasi tertinggi (57.8%), tetapi akurasi keseluruhan tetap terbatas.

## Catatan

- Ini challenge terkontrol, bukan ulasan konsumen yang ditinjau manusia.
- Label challenge tidak dipakai untuk fine-tuning atau memilih model.
- Label latih berasal dari data sintetis proyek; performa ini tidak bisa digeneralisasi ke data pasar nyata.
- Checkpoint fine-tuned lokal tersimpan di `tmp/indobert-cafestock-fourclass` dan dimuat oleh endpoint demo.
- Bobot 498 MB tidak disimpan di GitHub. Jalankan `experiment_indobert.py` untuk membuatnya kembali; proses memerlukan unduhan base model dan sekitar 30 menit di CPU.
- Seri sentimen historis dan fitur risiko tetap memakai SVM kronologis; endpoint form teks memakai IndoBERT.
