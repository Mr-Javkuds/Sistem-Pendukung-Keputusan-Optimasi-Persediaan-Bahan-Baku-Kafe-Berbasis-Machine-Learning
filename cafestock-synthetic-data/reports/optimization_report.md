# Tahap 10 â€” peramalan kebutuhan dan optimasi kebijakan

Target kebutuhan dibentuk dari permintaan laten Ã— resep, bukan penjualan terpenuhi atau jumlah baseline. Target rata-rata harian mencakup min(lead time + 2, masa simpan) hari; jendela lintas split dikeluarkan.
Regresi Random Forest dibandingkan rata-rata konsumsi historis; MAE/RMSE per bahan dalam satuan masing-masing ada di [JSON](optimization_report.json).

Kandidat ML terpilih pada validation: **ML_1.2**. Kebijakan rekomendasi setelah dibandingkan baseline pada validation: **ML_1.2**.

| Kebijakan | Fill rate test | Stockout transaksi test | Limbah test (IDR) | Biaya tujuan test (IDR) |
|---|---:|---:|---:|---:|
| baseline | 0.9057 | 0.0924 | 1097280 | 122440017 |
| ML_0.8 | 0.8270 | 0.1683 | 749360 | 150191813 |
| ML_1.0 | 0.9616 | 0.0398 | 1416600 | 101146288 |
| ML_1.2 | 0.9917 | 0.0094 | 2469040 | 90933804 |

## Asumsi dan interpretasi

- Same latent demand and discrepancy random seed for every replay.
- FEFO, lead time, MOQ, package size, shelf life and pipeline stock enforced by shared simulator.
- Lost revenue is an assumed shortage penalty, not measured profit. No fixed ordering fee.
- Forecast target uses simulated latent demand; a real cafe needs records of unmet demand.
- Forecast train excludes target windows beyond its partition; validation selects safety factor.
- Policy replay before validation is warm-up; performance is claimed only on held-out test.
- Optimization searches three safety factors; it does not prove a global optimum.

Biaya tujuan = biaya bahan terpakai/limbah/selisih + biaya simpan harian 0,1% nilai stok akhir + nilai penjualan tidak terpenuhi. Biaya limbah sudah termasuk biaya bahan, tidak dijumlahkan dua kali. Nilai stok awal dan akhir tidak dianggap habis terpakai.
Semua kebijakan disimulasikan ulang sepanjang periode. Riwayat konsumsi diperbarui dari hasil kebijakannya sendiri, bukan memakai ledger baseline untuk menilai kebijakan baru.
Rekomendasi terakhir berada di [CSV](../prepared/10_optimization/owner_recommendations.csv); belum merupakan pesanan kepada pemasok.
