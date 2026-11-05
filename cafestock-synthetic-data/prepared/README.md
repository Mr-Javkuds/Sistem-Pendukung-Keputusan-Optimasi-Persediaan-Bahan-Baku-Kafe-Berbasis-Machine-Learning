# Prepared stages 01–05

Artefak ini dibuat oleh `audit_steps_1_5.py` setelah generator dan validator selesai.
`source_generation_manifest.json` mengikat versi input/output/config yang dipakai.
Jalankan ulang audit jika output generator berubah; jangan mencampur prepared
artifacts dari generasi lain.

- `01_raw_dataset/table_inventory.csv`: tabel, jumlah baris/kolom dan hash output.
- `02_data_cleaning/cleaning_summary.json`: perlakuan NULL, duplikasi dan eligibility.
- `03_eda/eda_summary.json`: statistik outcome dari train saja; grafik di reports/eda/.
- `04_feature_engineering/contracts.json`: sumber, fitur X dan target y tiap tugas.
- `05_split_70_15_15/<task>/`: train/validation/test dengan X, y dan metadata
  terpisah; urutan baris sama pada ketiga file dalam satu partisi.
- `artifact_manifest.json`: hash dan ukuran 36 CSV X/y/metadata hasil ekspor.

Tidak ada TF-IDF/encoder/imputer yang di-fit dan tidak ada model yang dilatih.
Tugas sentiment hanya memakai training_status=eligible, risiko/tren hanya target
yang lengkap, restock_reference hanya meniru aturan baseline (bukan optimalisasi).
Proporsi nominal 70/15/15 didasarkan pada waktu dan berubah setelah dedup/purge/
censoring. Metadata ID, fingerprint, split, dan waktu label bukan fitur model.
