"""Completion gate: execute tests, reconcile metrics, bind source/artifact hashes."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import importlib.metadata
import pandas as pd
from sklearn.metrics import f1_score, average_precision_score
from encode import verify_upstream

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    verify_upstream(ROOT)
    result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (ROOT/'reports/completion_tests.txt').write_text(result.stdout, encoding='utf-8')
    if result.returncode:
        raise RuntimeError('Tests failed; see reports/completion_tests.txt')
    modeling = json.loads((ROOT/'reports/modeling_report.json').read_text())
    for name, row in modeling['risk'].items():
        predictions = pd.read_csv(ROOT/'prepared/07_modeling'/f'{name}_test_predictions.csv')
        assert abs(f1_score(predictions.target_stockout, predictions.prediction) - row['test']['f1']) < 1e-12
        assert abs(average_precision_score(predictions.target_stockout, predictions.risk_score) - row['test']['pr_auc_average_precision']) < 1e-12
    browser = json.loads((ROOT/'reports/app/browser_check.json').read_text())
    assert browser['passed']
    for name, expected in browser['source_sha256'].items():
        assert sha(ROOT/name) == expected, 'Browser evidence is stale; rerun verify_browser.py'
    required = ['SVM.joblib', 'NaiveBayes.joblib', 'D_combined_RandomForest.joblib',
                'D_combined_LogisticRegression.joblib', 'permutation_importance.csv', 'sentiment_terms.json']
    assert all((ROOT/'prepared/07_modeling'/name).exists() for name in required)
    validation = (ROOT/'reports/validation_report.md').read_text(encoding='utf-8')
    assert '374/374 checks passed' in validation
    inventory = {}
    for folder in ('prepared/07_modeling', 'prepared/10_optimization'):
        for path in sorted((ROOT/folder).rglob('*')):
            if path.is_file():
                inventory[path.relative_to(ROOT).as_posix()] = sha(path)
    for name in ('train_models.py', 'optimize_inventory.py', 'owner_app.py', 'verify_completion.py',
                 'analyze_results.py', 'reports/error_analysis.md', 'src/simulate_inventory.py', 'web/index.html', 'reports/modeling_report.json',
                 'reports/optimization_report.json'):
        inventory[name] = sha(ROOT/name)
    report = {'status': 'passed', 'scope': 'academic synthetic-data prototype, stages 01–11',
        'test_exit_code': result.returncode, 'browser': browser,
        'risk_metrics_independently_recomputed': len(modeling['risk']),
        'versions': {name: importlib.metadata.version(name) for name in ('numpy', 'pandas', 'scikit-learn', 'scipy', 'joblib')},
        'generation_manifest_sha256': sha(ROOT/'reports/generation_manifest.json'),
        'artifact_sha256': inventory}
    (ROOT/'reports/completion_manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    optimization = json.loads((ROOT/'reports/optimization_report.json').read_text())
    primary = modeling['risk']['D_combined_RandomForest']['test']
    chosen = optimization['recommended_policy']
    before = optimization['policies']['baseline']['test']
    after = optimization['policies'][chosen]['test']
    lines = ['# Audit penyelesaian tahap 01–11', '',
        'Lingkup: prototipe akademik lokal berbasis data sintetis. Tidak mencakup scraper Instagram nyata, pengadaan pemasok langsung, atau deployment publik.', '',
        '| Tahap | Bukti |', '|---|---|',
        '| 01–05 | [239/239 audit](steps_1_5_audit.md), manifest data, X/y/metadata terpisah |',
        '| 06 | [196/196 encoding](encoding_report.md), transformer train-only, matriks per split |',
        '| 07 | [Model tersimpan dan laporan pelatihan](modeling_report.md) |',
        '| 08 | Metrik per kelas, threshold validation, sepuluh kombinasi ablation/model, prediksi test; F1/AP dihitung ulang oleh gate |',
        '| 09 | Permutation importance, kata pendukung SVM, prediksi aktual/salah untuk analisis kesalahan |',
        '| 10 | Target kebutuhan dari latent demand × resep, forecast MAE/RMSE per bahan, empat replay kebijakan, seleksi validation |',
        '| 11 | [Panduan aplikasi](../docs/aplikasi_pemilik.md), tes HTTP, [Chrome desktop/seluler](app/browser_check.json) |', '',
        '## Pemeriksaan akhir', '',
        '- Unit/integration tests: lulus; [output aktual](completion_tests.txt).',
        '- Validasi dataset: 374/374; hash data sumber tetap cocok manifest tahap persiapan.',
        '- Semua prediksi sentimen historis dilatih pada label dari batch lebih awal; batch warm-up tidak diberi sentimen palsu.',
        '- Replay baseline cocok dengan snapshot inventori asli. Seluruh kebijakan mempertahankan keseimbangan stok, nonnegativitas, MOQ dan kemasan.',
        '- Target kebutuhan diperiksa ulang dari permintaan laten; jendela target lintas split dikeluarkan.',
        '- HTTP: tiga cabang, CSV, inferensi, persetujuan lokal persisten/idempoten, input invalid, origin lintas situs.',
        '- Chrome: cabang, inferensi, unduhan, tanpa error JS, layout seluler tanpa overflow halaman.',
        '- Hash kode, model, prediksi, dan hasil replay: [completion_manifest.json](completion_manifest.json).', '',
        'Analisis kesalahan per bahan dan contoh false negative: [error_analysis.md](error_analysis.md).', '',
        '## Hasil utama', '',
        f"- SVM macro F1 test: {modeling['sentiment']['SVM']['test']['macro avg']['f1-score']:.4f}; teks template sintetis mudah diklasifikasi, bukan bukti performa Instagram nyata.",
        f"- Random Forest gabungan: F1 {primary['f1']:.4f}, AP {primary['pr_auc_average_precision']:.4f} pada test.",
        f"- Kebijakan {chosen}, dipilih pada validation: fill rate test {before['fill_rate']:.2%} → {after['fill_rate']:.2%}.",
        f"- Biaya tujuan test: IDR {before['objective_cost_idr']:,.0f} → {after['objective_cost_idr']:,.0f}; biaya limbah IDR {before['waste_cost_idr']:,.0f} → {after['waste_cost_idr']:,.0f}.", '',
        '## Batas penelitian', '',
        'Hasil menunjukkan perilaku simulator dan asumsi biaya. Optimasi hanya menelusuri tiga faktor stok pengaman, bukan optimum global. Sentimen tidak dipaksakan memengaruhi permintaan. Model stok menilai kebijakan historis; aplikasi memisahkan skor itu dari rekomendasi hasil replay. Akurasi, popularitas, laba, dan sebab-akibat bisnis nyata belum dibuktikan.',
        'Alamat/lisensi sumber eksternal belum sepenuhnya terdokumentasi pada audit awal; ini tetap keterbatasan akademik. Tidak ada sumber atau izin baru yang direkayasa.', '',
        '## Menjalankan ulang', '', '```powershell',
        '../.venv/Scripts/python.exe train_models.py', '../.venv/Scripts/python.exe optimize_inventory.py',
        '../.venv/Scripts/python.exe analyze_results.py', '../.venv/Scripts/python.exe -m src.validate', '../.venv/Scripts/python.exe owner_app.py',
        '# Pada terminal lain, dengan dependensi browser tersedia:',
        '../.venv/Scripts/python.exe verify_browser.py', '../.venv/Scripts/python.exe verify_completion.py', '```']
    (ROOT/'reports/completion_report.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('PASS: stages 01–11 completion gate; see reports/completion_report.md')


if __name__ == '__main__':
    run()
