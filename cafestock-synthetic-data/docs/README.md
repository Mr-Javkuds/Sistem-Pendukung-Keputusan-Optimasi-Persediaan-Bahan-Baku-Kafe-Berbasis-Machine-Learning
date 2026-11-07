# Panduan dokumentasi CafeStock

[README utama](../../README.md) · [Cara menjalankan proyek](../README.md)

## Urutan membaca

Baru mengenal proyek? Mulai dari [README utama](../../README.md), lalu lihat
[alur tahap 01–11](alur_project_ml.md). Untuk menjalankan dashboard, ikuti
[panduan aplikasi](aplikasi_pemilik.md).

| Kebutuhan | Dokumen |
|---|---|
| Progres dan bukti penyelesaian | [Alur proyek ML](alur_project_ml.md) |
| Sumber data dan batas penelitian | [Asumsi dan provenance](assumptions.md) |
| Postingan, menu, wilayah, dan sentimen | [Dataset sentimen pasar menu](sentimen_pasar_menu.md) |
| Hubungan antartabel | [ERD](erd.md) |
| Arti kolom dan satuan | [Kamus data](data_dictionary.md) |
| Fitur yang boleh masuk model | [Kontrak fitur JSON](feature_manifest.json) |
| Partisi X/y/metadata | [Panduan prepared data](../prepared/README.md) |
| Matriks dan preprocessing tahap 06 | [Panduan encoding](../prepared/06_encoding/README.md) |

## Bukti pemeriksaan

| Laporan | Cakupan |
|---|---|
| [Audit tahap 01–05](../reports/steps_1_5_audit.md) | Persiapan, cleaning, fitur, dan split |
| [EDA](../reports/eda_report.md) | Pola deskriptif data train |
| [Encoding](../reports/encoding_report.md) | Preprocessing yang di-fit hanya pada train |
| [Validasi](../reports/validation_report.md) | Konsistensi data dan aturan waktu |
| [Reproduksibilitas](../reports/reproducibility_report.md) | Kesamaan CSV pada dua generasi |
| [PostgreSQL](../reports/postgres_verification.md) | Impor tabel dan constraint |
| [Audit sumber](../reports/source_audit.md) | Asal dan keterbatasan input |
| [Profil statistik](../reports/statistical_profile.md) | Ringkasan distribusi data |
| [Migrasi Semarang](../reports/semarang_migration.md) | Perubahan dari rancangan awal |
| [Challenge sentimen 2.000 teks](../reports/sentiment_stress_test/report.md) | Kelemahan model SVM pada variasi kalimat |
| [Eksperimen IndoBERT](../reports/indobert_experiment/report.md) | Perbandingan per kelas, batas, dan checkpoint lokal |
| [Audit keterbacaan UI](../reports/ui_readability_review.md) | Perubahan antarmuka dan pemeriksaan visual |

Laporan membuktikan pelaksanaan pada data/config tertentu. Perubahan data perlu
diikuti pemeriksaan ulang. Jumlah pemeriksaan bukan akurasi machine learning.
Laporan yang dihasilkan script dapat ditulis ulang ketika script dijalankan lagi.

## Istilah singkat

- **Sintetis:** dihasilkan simulator, bukan pengamatan kafe atau Instagram nyata.
- **Provenance:** catatan asal dan cara data dibuat.
- **Stockout:** kekurangan bahan sehingga permintaan tidak sepenuhnya terpenuhi.
- **Leakage:** informasi yang belum tersedia saat keputusan masuk ke eksperimen.
- **Purge:** mengeluarkan baris dengan jendela target yang melintasi batas partisi.
- **Ablation:** membandingkan model dengan dan tanpa kelompok fitur tertentu.
- **Baseline:** aturan/model pembanding; belum berarti solusi optimal.

## Referensi historis

[Master prompt awal](../../master_prompt.md) merupakan arsip rancangan. Untuk
implementasi aktif, ikuti skenario Semarang dan Instagram sintetis di dokumen ini.

## Hasil tahap 07–11

- [Pelatihan, evaluasi, ablation, dan explainability](../reports/modeling_report.md).
- [Peramalan kebutuhan bahan dan optimasi kebijakan](../reports/optimization_report.md).
- [Aplikasi pemilik dan cara menjalankannya](aplikasi_pemilik.md).
- [Audit penyelesaian dan keterbatasan prototipe](../reports/completion_report.md).

Form analisis teks di dashboard menggunakan IndoBERT fine-tuned empat kelas.
Bobotnya tidak ikut repository karena berukuran besar; jalankan eksperimen sesuai
[panduan aplikasi](aplikasi_pemilik.md) untuk membuat checkpoint lokal. Seri
sentimen pada grafik historis tetap memakai prediksi SVM yang dipakai pipeline
risiko. Kedua jalur ini berbeda dan hasilnya tidak boleh dianggap sama.
