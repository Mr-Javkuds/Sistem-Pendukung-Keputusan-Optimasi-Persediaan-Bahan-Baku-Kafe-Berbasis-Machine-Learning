"""Frozen 2,000-case Indonesian sentiment challenge. Never used for fitting.

400 controlled semantic scenarios x five surface variants. Gold labels are
author-defined by the rubric, not independent human annotations or real reviews.
The saved production SVM is evaluated unchanged, both in batch and over HTTP.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
import argparse
import hashlib
import json
import re
import time
import unicodedata
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'reports/sentiment_stress_test'
LABELS = ['positive', 'negative', 'neutral', 'mixed']
MENUS = ['es latte', 'matcha latte', 'cokelat panas', 'teh chai', 'kopi seduh']

TASTE_POSITIVE = [
    'rasanya lezat dan membuat saya ingin pesan lagi',
    'racikan rasanya pas sekali di lidah saya',
    'saya suka aroma dan rasanya yang nikmat',
    'tidak mengecewakan, rasanya justru memuaskan',
    'nggak bikin enek, rasanya bikin nagih',
    'bukan cuma wangi, rasanya juga enak',
    'aftertaste-nya nyaman dan saya menikmatinya',
    'teksturnya lembut, setiap teguk terasa menyenangkan',
    'rasanya mantul dan beneran cocok sama selera gue',
    'aromanya harum dan rasanya benar-benar istimewa',
]
TASTE_NEGATIVE = [
    'rasanya tidak enak dan saya tidak mau pesan lagi',
    'racikannya hambar sehingga saya kecewa',
    'aromanya tengik dan membuat saya mual',
    'rasanya mengecewakan, jauh dari yang saya harapkan',
    'nggak cocok di lidah gue, malah bikin enek',
    'bukan rasa yang saya suka, rasanya terlalu getir',
    'aftertaste-nya mengganggu dan tidak nyaman diminum',
    'teksturnya menggumpal dan sulit saya nikmati',
    'rasane ora enak, saya kapok meminumnya',
    'rasa gosongnya sangat dominan dan saya tidak menyukainya',
]
VALUE_POSITIVE = [
    'harganya terjangkau dan pantas untuk kualitas ini',
    'porsi sebanyak ini terasa sangat sepadan dengan uangnya',
    'harganya tidak mahal dan saya puas dengan nilainya',
    'menurut saya ini layak dibeli lagi dengan harga tersebut',
    'biayanya ramah di kantong untuk porsi yang saya dapat',
    'saya merasa uang yang dikeluarkan tidak sia-sia',
    'porsinya melimpah dan harganya bersahabat',
    'bukan harga yang memberatkan, menurut saya ekonomis',
    'hargane murah, worth it buat porsi segini',
    'perbandingan harga dan kualitasnya membuat saya puas',
]
VALUE_NEGATIVE = [
    'harganya kelewat mahal untuk porsi sekecil ini',
    'saya merasa rugi karena porsinya tidak sepadan dengan harga',
    'harga seperti ini tidak masuk akal bagi saya',
    'biayanya terlalu tinggi sehingga tidak layak dibeli lagi',
    'porsinya mengecewakan untuk uang yang sudah saya keluarkan',
    'saya menyesal membayar sebanyak ini untuk porsi yang sedikit',
    'harganya tidak terjangkau dan terlalu membebani kantong',
    'menurut saya harga ini bukan penawaran yang bagus, malah kemahalan',
    'hargane larang banget, ora worth it kanggo aku',
    'nilai yang saya dapat buruk dibandingkan biaya pembeliannya',
]
NEUTRAL_A = [
    'tercantum dalam daftar minuman hari ini',
    'dipesan dua gelas pada pukul tiga sore',
    'namanya tertulis di papan menu dekat kasir',
    'tersedia dalam ukuran reguler dan besar',
    'dicatat sebagai salah satu menu dalam laporan hari ini',
    'belum saya coba sehingga saya belum menilai rasanya',
    'sedang saya tanyakan komposisi bahannya kepada barista',
    'ada di daftar pesanan yang sedang saya periksa',
    'disebut dalam percakapan kami tentang jenis minuman',
    'difoto untuk mendokumentasikan daftar menu',
]
NEUTRAL_B = [
    'harga yang tertera pada daftar adalah Rp25.000',
    'saya belum punya pendapat tentang harga atau kualitasnya',
    'jumlah yang dicatat dalam pesanan adalah tiga gelas',
    'nama menu dan ukurannya akan saya masukkan ke tabel',
    'saya sedang mencari informasi mengenai kandungan gulanya',
    'belum ada penilaian pribadi saya tentang menu ini',
    'saya ingin mengetahui apakah ada pilihan tanpa susu',
    'informasi bahan akan saya baca sebelum memutuskan pesanan',
    'pesanan ini tercatat atas nama kelompok kami',
    'catatan tersebut berisi nama minuman, jumlah, dan ukuran gelas',
]


def normalize(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', text).casefold()).strip()


def variants(text):
    slang = text.replace('saya', 'aku').replace('tidak', 'nggak').replace('harganya', 'hargane')
    slang = slang.replace('sehingga', 'jadinya').replace('dengan', 'sama').replace('benar-benar', 'bener-bener')
    # Corrupt one non-negator token. This never deletes/reverses a sentiment cue.
    excluded = {'tidak', 'bukan', 'nggak', 'tanpa', 'belum', 'jangan'}
    candidates = [m for m in re.finditer(r'\b[a-z]{7,}\b', text) if m.group() not in excluded]
    typo = text
    if candidates:
        token = candidates[-1]
        value = token.group()
        typo = text[:token.start()] + value[:2] + value[3:] + text[token.end():]
    return [
        ('formal', text),
        ('informal', 'Kalau menurut aku, ' + slang[0].lower() + slang[1:]),
        ('casing_punctuation', 'CATATAN MENU: ' + text.upper().replace(';', '...')),
        ('typo', 'Pengalaman pesan kali ini: ' + typo[0].lower() + typo[1:]),
        ('social_context', 'Obrolan menu di Semarang. ' + text + ' #ceritamenu #minuman'),
    ]


def build_cases():
    cores = []
    for label, first, second in [('positive', TASTE_POSITIVE, VALUE_POSITIVE),
                                  ('negative', TASTE_NEGATIVE, VALUE_NEGATIVE),
                                  ('neutral', NEUTRAL_A, NEUTRAL_B)]:
        for i, a in enumerate(first):
            for j, b in enumerate(second):
                menu = MENUS[(i+j) % len(MENUS)]
                connector = '; ' if label == 'neutral' else '. Selain itu, '
                text = f'Untuk {menu}, {a}{connector}{b}.'
                cores.append((label, f'{label}_{i:02d}_{j:02d}', text, 'factual_no_opinion' if label=='neutral' else
                              'negation_or_scope' if i in (3,4,5) or j in (2,5,7) else 'direct_opinion'))
    for orientation, first, second in [('taste_positive_value_negative', TASTE_POSITIVE, VALUE_NEGATIVE[:5]),
                                       ('taste_negative_value_positive', TASTE_NEGATIVE, VALUE_POSITIVE[:5])]:
        for i, a in enumerate(first):
            for j, b in enumerate(second):
                menu = MENUS[(i+j) % len(MENUS)]
                text = f'{menu.capitalize()} ini {a}, tetapi {b}.'
                cores.append(('mixed', f'mixed_{orientation}_{i:02d}_{j:02d}', text, orientation))
    rows = []
    for label, core, text, phenomenon in cores:
        for variant, content in variants(text):
            rows.append({'case_id': f'CASE-{len(rows)+1:04d}', 'scenario_id': core,
                'variant': variant, 'phenomenon': phenomenon, 'content_text': content,
                'expected_label': label, 'label_provenance': 'controlled_author_rubric'})
    cases = pd.DataFrame(rows)
    assert len(cases) == 2000 and cases.scenario_id.nunique() == 400
    assert cases.content_text.nunique() == 2000
    assert cases.content_text.map(normalize).nunique() == 2000
    assert cases.expected_label.value_counts().eq(500).all()
    return cases


def call_api(base_url, row):
    started = time.perf_counter()
    try:
        payload = json.dumps({'text': row.content_text}).encode('utf-8')
        request = Request(base_url.rstrip('/')+'/api/sentiment', data=payload,
                          headers={'Content-Type':'application/json'})
        with urlopen(request, timeout=30) as response:
            label = json.load(response)['label']
        return {'case_id': row.case_id, 'api_label': label, 'api_error': '',
                'api_latency_ms': (time.perf_counter()-started)*1000}
    except Exception as error:
        return {'case_id': row.case_id, 'api_label': None, 'api_error': str(error),
                'api_latency_ms': (time.perf_counter()-started)*1000}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8765')
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    cases = build_cases()
    path = OUT/'cases_2000.csv'
    cases.to_csv(path, index=False, lineterminator='\n')
    source = ROOT/'prepared/07_modeling/SVM.joblib'
    manifest = {'case_count':len(cases), 'semantic_scenarios':400, 'cases_sha256':digest(path),
        'model_sha256_before':digest(source), 'seed':'deterministic, no random sampling',
        'rubric': {'positive':'Explicit favorable taste/value, no contrary menu judgment.',
                   'negative':'Explicit unfavorable taste/value, no favorable menu judgment.',
                   'neutral':'Menu facts or questions without personal favorable/unfavorable judgment.',
                   'mixed':'Explicit favorable and unfavorable judgments on the same menu across taste/value.'},
        'limitations': ['400 controlled semantic scenarios, each with five surface variants; not 2000 independent human reviews.',
                       'Labels were authored before prediction; no independent annotator adjudication.',
                       'Cases are constructed Indonesian texts, not collected Instagram content.',
                       'This is a frozen-model challenge audit; no training, tuning, or endpoint model replacement.']}
    # Freeze reference labels and data hash before even loading the model.
    (OUT/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    model = joblib.load(source)
    cases['prediction'] = model.predict(cases.content_text)
    cases['correct'] = cases.expected_label.eq(cases.prediction)
    processor = model.named_steps['tfidf']
    analyzer = processor.build_analyzer()
    cases['oov_fraction'] = cases.content_text.map(lambda text:
        sum(t not in processor.vocabulary_ for t in analyzer(text))/max(1,len(analyzer(text))))
    train = pd.read_csv(ROOT/'prepared/05_split_70_15_15/sentiment/train_X.csv')
    overlap = cases.content_text.map(normalize).isin(set(train.content_text.map(normalize)))
    assert not overlap.any(), 'Challenge contains a verbatim normalized training text'
    api_summary = {'executed':False}
    if not args.offline:
        print('Sending all 2000 cases through the live HTTP endpoint...', flush=True)
        with ThreadPoolExecutor(max_workers=4) as pool:
            api = pd.DataFrame(pool.map(lambda row: call_api(args.base_url, row), cases.itertuples()))
        cases = cases.merge(api, on='case_id', validate='one_to_one')
        valid = cases.api_label.isin(LABELS)
        api_summary = {'executed':True, 'requests':len(cases), 'successful':int(valid.sum()),
            'errors':int((~valid).sum()), 'matches_frozen_batch_model':int((cases.api_label==cases.prediction).sum()),
            'accuracy':float(cases.loc[valid,'api_label'].eq(cases.loc[valid,'expected_label']).mean()) if valid.any() else None,
            'latency_median_ms':float(cases.api_latency_ms.median()),
            'latency_p95_ms':float(cases.api_latency_ms.quantile(.95))}
    assert digest(source) == manifest['model_sha256_before'], 'Model changed during evaluation'
    report = {'accuracy':float(accuracy_score(cases.expected_label,cases.prediction)),
        'macro_f1':float(f1_score(cases.expected_label,cases.prediction,average='macro')),
        'classification_report':classification_report(cases.expected_label,cases.prediction,labels=LABELS,output_dict=True,zero_division=0),
        'confusion_matrix':confusion_matrix(cases.expected_label,cases.prediction,labels=LABELS).tolist(),
        'label_order':LABELS, 'api':api_summary,
        'by_variant':{name:{'count':len(g),'accuracy':float(g.correct.mean())} for name,g in cases.groupby('variant')},
        'by_phenomenon':{name:{'count':len(g),'accuracy':float(g.correct.mean())} for name,g in cases.groupby('phenomenon')},
        'mean_oov_fraction':float(cases.oov_fraction.mean()),
        'all_five_variants_correct_scenarios':int(cases.groupby('scenario_id').correct.all().sum()),
        'scenario_count':400, 'training_text_overlap':int(overlap.sum()),
        'model_sha256_after':digest(source), 'reference_cases_sha256':digest(path)}
    cases.to_csv(OUT/'predictions_2000.csv',index=False,lineterminator='\n')
    errors = cases[~cases.correct]
    errors.to_csv(OUT/'errors.csv',index=False,lineterminator='\n')
    (OUT/'results.json').write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    lines = ['# Uji tantangan sentimen — 2.000 input', '',
        '**Label acuan ditetapkan sebelum prediksi; model produksi tidak dilatih ulang atau diganti.**', '',
        '400 skenario makna × 5 variasi bahasa menghasilkan 2.000 teks unik, juga unik setelah NFKC/casefold/normalisasi spasi. Masing-masing kelas berisi 500 input. Tidak ada teks yang sama persis dengan train setelah normalisasi.',
        'Ini uji terkontrol buatan penulis, bukan 2.000 ulasan manusia independen. Label mengikuti rubric positif/negatif/netral/campuran rasa dan nilai; belum ditinjau anotator independen.', '',
        f"Akurasi challenge: **{report['accuracy']:.2%}**. Macro F1: **{report['macro_f1']:.4f}**. Salah: **{len(errors):,} / 2.000**.", '',
        '| Kelas acuan | Precision | Recall | F1 | Jumlah |', '|---|---:|---:|---:|---:|']
    for label in LABELS:
        m = report['classification_report'][label]
        lines.append(f"| {label} | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1-score']:.4f} | {m['support']:.0f} |")
    lines += ['', '## Matriks kebingungan', '', 'Baris = acuan; kolom = prediksi.', '',
              '| Acuan / prediksi | positive | negative | neutral | mixed |', '|---|---:|---:|---:|---:|']
    for label, counts in zip(LABELS, report['confusion_matrix']):
        lines.append('| '+label+' | '+' | '.join(map(str,counts))+' |')
    lines += ['', '## Variasi bahasa', '', '| Variasi | Jumlah | Akurasi |', '|---|---:|---:|']
    for name,row in report['by_variant'].items():
        lines.append(f"| {name} | {row['count']} | {row['accuracy']:.2%} |")
    lines += ['', '## Pola makna', '', '| Pola | Jumlah | Akurasi |', '|---|---:|---:|']
    for name,row in report['by_phenomenon'].items():
        lines.append(f"| {name} | {row['count']} | {row['accuracy']:.2%} |")
    lines += ['', '## Endpoint aplikasi', '', '```json',json.dumps(api_summary,indent=2),'```', '',
        '## Contoh kesalahan (variasi formal)', '', '| Teks | Acuan | Prediksi |', '|---|---|---|']
    for label in LABELS:
        for row in errors[errors.expected_label.eq(label)&errors.variant.eq('formal')].head(4).itertuples():
            lines.append(f'| {row.content_text} | {row.expected_label} | {row.prediction} |')
    lines += ['', '## Diagnosis dan batas', '',
        'Generator latih hanya mempunyai empat pola rasa positif, empat negatif, empat netral, dan tiga kalimat nilai/harga. Mixed latih selalu rasa positif + harga negatif. Arah sebaliknya tidak diajarkan. Test lama berasal dari generator yang sama, sehingga skor 1,0 tidak mengukur generalisasi bahasa bebas.',
        f"Rata-rata n-gram yang tidak ada dalam kosakata model: {report['mean_oov_fraction']:.2%}. Seluruh lima variasi benar pada {report['all_five_variants_correct_scenarios']} dari 400 skenario. Angka ini bukan interval kepercayaan atas populasi ulasan nyata.",
        'Negasi, bahasa informal, typo, fakta netral dan mixed arah terbalik perlu tercakup pada data anotasi yang lebih beragam. Challenge ini harus tetap terpisah dari train/tuning; jika dipakai merancang perbaikan, perlukan test baru yang belum dilihat untuk klaim akurasi berikutnya.',
        'Belum ada klaim bahwa sarana demo ini siap untuk ulasan nyata. Tidak ada perubahan otomatis pada classifier, grafik, fitur stok, atau model produksi.', '',
        '[Seluruh input dan acuan](cases_2000.csv) · [Prediksi lengkap](predictions_2000.csv) · [Semua kesalahan](errors.csv) · [Hasil JSON](results.json) · [Rubrik dan hash](manifest.json)']
    (OUT/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'accuracy':report['accuracy'],'macro_f1':report['macro_f1'],
                      'wrong':len(errors),'api':api_summary},indent=2),flush=True)


if __name__ == '__main__':
    run()
