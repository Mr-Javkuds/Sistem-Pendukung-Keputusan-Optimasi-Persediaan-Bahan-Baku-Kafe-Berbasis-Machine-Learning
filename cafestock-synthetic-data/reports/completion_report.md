# Audit penyelesaian tahap 01–11

Lingkup: prototipe akademik lokal berbasis data sintetis. Tidak mencakup scraper Instagram nyata, pengadaan pemasok langsung, atau deployment publik.

| Tahap | Bukti |
|---|---|
| 01–05 | [239/239 audit](steps_1_5_audit.md), manifest data, X/y/metadata terpisah |
| 06 | [196/196 encoding](encoding_report.md), transformer train-only, matriks per split |
| 07 | [Model tersimpan dan laporan pelatihan](modeling_report.md) |
| 08 | Metrik per kelas, threshold validation, sepuluh kombinasi ablation/model, prediksi test; F1/AP dihitung ulang oleh gate |
| 09 | Permutation importance, kata pendukung SVM, prediksi aktual/salah untuk analisis kesalahan |
| 10 | Target kebutuhan dari latent demand × resep, forecast MAE/RMSE per bahan, empat replay kebijakan, seleksi validation |
| 11 | [Panduan aplikasi](../docs/aplikasi_pemilik.md), endpoint lokal, [cuplikan dashboard](app/desktop.png) |

## Pemeriksaan akhir

- Unit/integration tests: lulus; [output aktual](completion_tests.txt).
- Validasi dataset: 374/374; hash data sumber tetap cocok manifest tahap persiapan.
- Semua prediksi sentimen historis dilatih pada label dari batch lebih awal; batch warm-up tidak diberi sentimen palsu.
- Replay baseline cocok dengan snapshot inventori asli. Seluruh kebijakan mempertahankan keseimbangan stok, nonnegativitas, MOQ dan kemasan.
- Target kebutuhan diperiksa ulang dari permintaan laten; jendela target lintas split dikeluarkan.
- HTTP: tiga cabang, CSV, inferensi, persetujuan lokal persisten/idempoten, input invalid, origin lintas situs.
- Chrome: cabang, inferensi, unduhan, tanpa error JS, layout seluler tanpa overflow halaman.
- Hash kode, model, prediksi, dan hasil replay: [completion_manifest.json](completion_manifest.json).

Catatan versi: hasil pemeriksaan di atas berasal dari snapshot sebelum perubahan
terbaru pada form IndoBERT dan grafik proyeksi pembelian. Untuk memeriksa snapshot
terkini, jalankan kembali pemeriksaan HTTP/unit dan `verify_browser.py`.

Analisis kesalahan per bahan dan contoh false negative: [error_analysis.md](error_analysis.md).

## Hasil utama

- SVM macro F1 test: 1.0000; teks template sintetis mudah diklasifikasi, bukan bukti performa Instagram nyata.
- Form teks demo kini memakai IndoBERT fine-tuned. Challenge terkontrol 2.000 kalimat: akurasi 54,70%, Macro F1 0,5084, recall positif 7,6%; lihat [laporan per kelas](indobert_experiment/report.md). Bobot checkpoint tidak disimpan di GitHub.
- Random Forest gabungan: F1 0.7753, AP 0.6876 pada test.
- Kebijakan ML_1.2, dipilih pada validation: fill rate test 90.57% → 99.17%.
- Biaya tujuan test: IDR 122,440,017 → 90,933,804; biaya limbah IDR 1,097,280 → 2,469,040.

## Batas penelitian

Hasil menunjukkan perilaku simulator dan asumsi biaya. Optimasi hanya menelusuri tiga faktor stok pengaman, bukan optimum global. Sentimen tidak dipaksakan memengaruhi permintaan. Model stok menilai kebijakan historis; aplikasi memisahkan skor itu dari rekomendasi hasil replay. Akurasi, popularitas, laba, dan sebab-akibat bisnis nyata belum dibuktikan.
Skor IndoBERT dihitung pada challenge buatan dan tidak boleh dianggap sebagai akurasi untuk konsumen nyata. Pipeline fitur historis/risk tetap memakai prediksi SVM kronologis; form demo menggunakan IndoBERT.
Alamat/lisensi sumber eksternal belum sepenuhnya terdokumentasi pada audit awal; ini tetap keterbatasan akademik. Tidak ada sumber atau izin baru yang direkayasa.

## Menjalankan ulang

```powershell
../.venv/Scripts/python.exe train_models.py
../.venv/Scripts/python.exe optimize_inventory.py
../.venv/Scripts/python.exe analyze_results.py
../.venv/Scripts/python.exe -m src.validate
../.venv/Scripts/python.exe owner_app.py
# Pada terminal lain, dengan dependensi browser tersedia:
../.venv/Scripts/python.exe verify_browser.py
../.venv/Scripts/python.exe verify_completion.py
```
