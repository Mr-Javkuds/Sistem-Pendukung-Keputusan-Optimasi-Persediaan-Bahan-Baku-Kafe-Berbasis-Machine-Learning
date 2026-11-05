# Audit tahap ML 01–05

239/239 pemeriksaan lulus.

| Tahap | Status | Bukti |
|---|---|---|
| 01 Raw dataset | PASS | 31/31 checks |
| 02 Data cleaning | PASS | 71/71 checks |
| 03 EDA | PASS | 3/3 checks |
| 04 Feature engineering | PASS | 19/19 checks |
| 05 Split 70/15/15 | PASS | 115/115 checks |

## Perbaikan cleaning
Ditemukan 1,944 kemunculan caption identik berulang. Teks ML memakai training_status=eligible; kemunculan lebih baru dipertahankan sebagai catatan tetapi dikeluarkan dari modeling. Tidak ada teks identik yang eligible pada dua partisi. Caption mentah dan agregat event tidak ditulis ulang.

## Baris siap modeling
| Tugas | Train | Validation | Test |
|---|---:|---:|---:|
| risk | 7470 | 1440 | 1410 |
| restock_reference | 7470 | 1440 | 1620 |
| sentiment | 3361 | 664 | 620 |
| trend | 144 | 28 | 28 |

Nominal 70/15/15 berdasarkan kalender; proporsi baris berubah setelah deduplikasi, purge dan censoring. restock_reference masih target aturan baseline, bukan optimasi. Tidak ada encoding yang di-fit atau model dilatih.

## Batas dan peringatan
- Source URLs/licenses are not fully documented; raw files and hashes exist, but source bibliography remains an academic limitation.
- Repeated synthetic captions are retained in market event tables; text-level ML excludes repeats. This is not an implemented Instagram spam detector.

## Pemeriksaan gagal
Tidak ada.

Rincian: steps_1_5_audit.json. EDA: eda_report.md. Prepared artifacts: ../prepared/artifact_manifest.json.