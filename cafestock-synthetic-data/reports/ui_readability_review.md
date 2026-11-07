# Audit dan perbaikan keterbacaan CafeStock

5 November 2026. Scope: aplikasi lokal, plain HTML/CSS/JavaScript, data dan pipeline ML dipertahankan.

Audit mengikuti [Web Interface Guidelines](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md) yang dibaca ulang untuk review ini, dan run app-screen pada skill design-taste-frontend.

## Hasil perubahan

- Navigasi tiga pekerjaan: analisis pasar, rencana pembelian, evaluasi & sentimen.
- Header, ringkasan, dan kontrol dipadatkan. Grafik desktop serta bahan yang perlu dibeli terlihat bersama.
- Empat seri tetap tersedia. Legenda memakai warna dan pola garis yang sama dengan grafik.
- SVG mengikuti lebar wadah; teks sumbu mempertahankan ukuran 12px pada ponsel.
- Metode, nilai asli, serta rincian menu tetap lengkap dalam disclosure.
- Header tabel numerik rata kanan, tabular figures, data hilang dibedakan dari nol.
- Tampilan tablet evaluasi menjadi satu kolom; tabel pembelian menjadi daftar pada ponsel.
- Skip link, fokus keyboard, label/name input, validasi teks inline dan tombol coba ulang tersedia.
- Cabang, view, kategori, periode, skala, seri terpilih, dan filter pembelian tersimpan pada URL.
- CSS dan skrip aplikasi dipisahkan agar perbaikan berikutnya mudah dibaca.

## Temuan yang diperbaiki, lokasi saat ini

```text
web/index.html:13 - skip link ke konten utama tersedia.
web/index.html:17 - navigasi tugas dengan tautan dan aria-current tersedia.
web/index.html:33 - status pemuatan analisis menggunakan aria-busy.
web/index.html:59 - form sentimen memiliki label, name, autocomplete, dan pesan aria-live.
web/dashboard.js:38 - URL menyimpan filter dan tampilan.
web/dashboard.js:105 - tanggal snapshot menggunakan Intl.DateTimeFormat dengan Asia/Jakarta.
web/dashboard.js:140 - teks kosong ditandai invalid dan fokus kembali ke textarea.
web/market_trends.js:141 - ResizeObserver menjaga skala SVG responsif dan sumbu terbaca.
```

## Sebelum dan sesudah

| Pemeriksaan | Sebelum | Sesudah |
|---|---|---|
| Judul desktop / ponsel | 32px / 27px | 24px / 22px |
| Ukuran huruf yang berbeda | 11 | 8 |
| Panjang tampilan analisis | 4,5 layar | sekitar 2,1 layar |
| Analisis: inspector | 0 FAIL, 4 WARN | 0 FAIL, 0 WARN |
| Evaluasi: inspector | panel tidak seimbang pada halaman lama | 0 FAIL, 0 WARN |
| Pembelian: inspector | bercampur dalam halaman panjang | 0 FAIL, 1 WARN yang dijelaskan |
| Seluler | sumbu mengecil, tabel hubungan terpotong | sumbu tetap terbaca, hubungan berupa baris berlabel |

Inspector dijalankan pada 1440, 768, dan 390px untuk setiap tampilan. Seluruh screenshot final dibuka, bukan hanya layar pertama.

## Arah dan critique

**Framed sheet**, seed **701885063**, tanpa redraw. Frame hijau-abu netral dari identitas CafeStock; Segoe UI dipertahankan agar offline. Tanda cs dan warna teal pada data utama membawa identitas produk. Elemen khusus produk adalah perbandingan empat sinyal pada minggu sama beserta antrian bahan dari resep kafe.

Pertanyaan utama: apakah pergerakan pasar sejalan dengan operasi cabang, dan bahan mana yang perlu dibeli?

Skor critique visual subjektif terakhir: design 8,5; usability 8,5; creativity 7,5; content 8,5; keseluruhan 8,4. Skor ini penilaian internal, bukan metrik pengguna.

Empat seri dengan pola berbeda dipertahankan sesuai permintaan pengguna. Warning purchase no-data-hue menghitung grafik dalam disclosure tertutup; tampilan utama pembelian berupa ledger netral tanpa status risiko yang perlu diberi warna. Bar pembelian tetap teal ketika alasan dibuka. Warning lint em-dash berasal dari placeholder nilai hilang, bukan tanda baca dekoratif.

Tidak ada foto, testimoni, statistik baru, atau dependency yang ditambahkan. Data tetap berasal dari simulasi proyek. Detail mingguan dapat digulir di dalam tabel berlabel ketika seluruh kolom tidak muat.

## Bukti

- [Inspector sebelum](../../.taste-skill/readability-before/report.json).
- [Inspector analisis final](../../.taste-skill/readability-after/report.json).
- [Inspector pembelian final](../../.taste-skill/readability-purchase-final/report.json).
- [Inspector evaluasi final](../../.taste-skill/readability-evaluation-final/report.json).
- [Direction dan critique lengkap](../../.taste-skill/readability-direction/review.md).
- [Uji Chrome aplikasi](app/browser_check.json).

Alur Chrome yang diuji: cabang, empat/dua seri, skala asli, 52 minggu, query state setelah reload, navigasi tugas, filter perlu dibeli, validasi teks, inferensi, ekspor CSV, error tren dan retry, keyboard skip link, serta tidak ada error JavaScript atau overflow halaman di ponsel. Pemeriksaan tambahan mencakup deep-link dua seri, error overview, mode reduced-motion, dan susunan tablet.
