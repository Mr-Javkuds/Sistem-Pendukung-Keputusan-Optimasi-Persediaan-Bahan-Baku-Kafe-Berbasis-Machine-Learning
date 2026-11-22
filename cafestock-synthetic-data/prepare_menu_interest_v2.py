"""Training-only contrast augmentation and a pre-locked synthetic confirmation set."""
from pathlib import Path
import ast
import base64
import csv
import hashlib
import io
import json
import unicodedata

ROOT=Path(__file__).resolve().parent
INTEREST=[
 'Aku berminat mencicipi {p}', 'Aku kepingin mencoba {p}', 'Aku ingin memesan {p} untuk dicoba',
 'Aku penasaran ingin merasakan {p}', 'Aku tertarik menikmati {p}', 'Ada keinginan dariku untuk mencoba {p}',
 'Aku berencana mencicipi {p}', 'Aku mau ikut mencoba {p}', 'Aku naksir {p} dan ingin mencicipinya',
 'Aku berharap bisa mencoba {p}', 'Aku punya minat untuk memesan {p}', 'Aku antusias untuk mencicipi {p}']
CERTAIN=['dan aku sudah yakin dengan keinginanku.', 'tanpa ada rasa ragu untuk mencoba.',
         'walaupun aku belum pernah membelinya.', 'meskipun belum pernah mencicipi, minatku sudah jelas.']
HESITATE=['namun aku masih ragu apakah akan cocok.', 'tetapi aku sekaligus enggan mencobanya.',
          'meski ada kekhawatiran yang membuatku bimbang.', 'tapi aku juga punya keberatan dan belum yakin memilihnya.']
REJECT=[
 'aku tidak tertarik mencoba {p}', 'aku tidak mau memesan {p}', 'aku tidak berminat mencicipi {p}',
 'aku memilih tidak mencoba {p}', 'aku ogah mencicipi {p}', 'aku menolak mencoba {p}',
 'aku sama sekali tidak ingin memesan {p}', 'aku tidak punya minat mencoba {p}',
 'aku tidak ada keinginan untuk mencicipi {p}', 'aku memutuskan melewatkan {p} karena tidak minat',
 'aku enggan mencoba {p} dan tidak berminat', 'aku tidak akan memilih {p} untuk dicicipi']
QUALITY=['Penampilannya menarik, tetapi ', 'Katanya rasanya enak, meskipun begitu ',
         'Banyak orang tertarik, namun ', 'Aku mengakui kualitasnya bagus, tetapi ']
NEUTRAL=[
 'Menurut penilaianku {p} rasanya enak.', 'Menurutku {p} rasanya tidak enak.', 'Aroma {p} harum tetapi rasanya pahit.',
 'Penyajian {p} cantik meskipun teksturnya kurang bagus.', 'Aku lebih suka rasa ringan dibandingkan {p}.',
 'Kualitas {p} mengecewakan menurut pengalamanku.', 'Untuk selera pribadiku {p} terlalu manis.',
 'Bisa jelaskan komposisi {p}?', 'Berapa ukuran porsi {p}?', 'Apakah {p} memakai bahan hewani?',
 'Topping {p} dari bahan apa?', 'Jam berapa {p} mulai tersedia?', 'Aku belum menyatakan ingin atau tidak ingin mencoba {p}.',
 'Harga {p} tinggi untuk ukuran sajian itu.', 'Aku cuma menilai rasa {p}, belum menyatakan ketertarikan.',
 'Untuk {p}, belum ada arah minat yang kusampaikan.']
NEUTRAL_END=['', ' Ini hanya komentar tentang produknya.', ' Belum ada pernyataan minat dariku.']

# Authored before tuning. These families are never used for augmentation or selection.
CONFIRM={
 'positive':[
  'Aku sudah menaruh {p} dalam rencana untuk kucicipi.', 'Ada hasrat untuk nyicip {p} dari diriku.',
  'Aku tertarik ikut menikmati sajian {p} ini.', 'Niatku jelas, aku mau mencicipi {p}.',
  'Aku ingin mencoba {p} kalau nanti berkesempatan mampir.', 'Bukan sekadar memuji, aku memang pengin nyobain {p}.',
  'Aku sudah mantap untuk mencoba {p}.', 'Aku belum pernah pesan, tetapi aku mau mencicipi {p}.',
  'Aku ingin memilih {p} sebagai menu yang akan kucoba.', 'Aku tidak ragu dengan minatku mencoba {p}.',
  'Keinginanku mencicipi {p} sudah ada.', 'Aku ada ketertarikan pribadi buat nyicip {p}.'],
 'negative':[
  'Aku memilih tak mencicipi {p} karena tidak berminat.', 'Tampilannya dipuji, tapi aku tetap ogah mencoba {p}.',
  'Aku sama sekali tidak mau menjadikan {p} menu cobaanku.', 'Tidak ada minat dariku untuk mencicipi {p}.',
  'Aku tidak ingin ikut memesan {p}.', 'Walau katanya enak, aku memilih tidak mencicipi {p}.',
  'Orang lain penasaran, aku justru tidak berminat mencoba {p}.', 'Aku menolak {p} sebagai pilihan untuk dicoba.',
  'Aku tidak memiliki keinginan untuk mencoba {p} sendiri.', 'Aku tidak tertarik ikut-ikutan nyicip {p}.',
  'Aku putuskan tidak memesan {p}, memang tidak ada minat.', 'Aku enggan mencicipi {p} dan tidak berniat mencoba.'],
 'neutral':[
  'Menurut lidahku {p} memiliki rasa yang lezat.', 'Sebagai penilaian kualitas, {p} kurang memuaskan.',
  'Untuk selera pribadiku {p} kemanisan.', 'Di atas {p} itu taburan apa namanya?',
  'Aku belum menyampaikan arah ketertarikanku pada {p}.', 'Sajian {p} ini mengandung apa saja?',
  'Rasa {p} sedap walaupun aromanya kurang menyenangkan.', 'Aku hanya menilai {p} enak, tanpa menyatakan ingin mencoba.',
  'Kritikku hanya kualitas {p}, bukan pernyataan mau atau menolak mencoba.', 'Yang kusampaikan hanya preferensi rasa tentang {p}.',
  'Apakah ada informasi ukuran {p}?', 'Aku belum menyatakan tertarik maupun menolak {p}.'],
 'mixed':[
  'Aku ada minat untuk nyicip {p}, tetapi rasa bimbang belum hilang.', 'Keinginanku mencoba {p} ada, bersamaan dengan rasa enggan.',
  'Aku ingin memilih {p}, hanya saja masih ragu dengan kecocokannya.', 'Aku mau mencicipi {p} meskipun masih diliputi keraguan.',
  'Aku tertarik ikut memesan {p}, namun ada keberatan yang membuatku bimbang.', 'Aku ingin mencoba {p}, tapi di sisi lain masih menolak.',
  'Aku mempunyai keinginan merasakan {p}, tetapi belum yakin.', 'Aku berminat mencoba {p} sambil masih meragukan pilihan itu.',
  'Niat mencicipi {p} ada, tetapi aku juga punya kekhawatiran.', 'Aku mau coba {p}, sekaligus merasa enggan mencicipinya.',
  'Aku ingin memesan {p} untuk dicoba, namun masih sangsi.', 'Aku punya minat mencicipi {p}, tapi ragu untuk benar-benar memilihnya.']}


def norm(s): return ' '.join(unicodedata.normalize('NFKC',str(s)).casefold().split())


def read(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def write(path,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def prepare(data,out):
    out.mkdir(parents=True,exist_ok=True)
    original=read(data/'train.csv');val=read(data/'validation.csv');legacy=read(data/'test.csv')
    products=read(data/'products.csv')
    forbidden={norm(json.loads(x['content_text'])['comment_text']) for x in val+legacy}
    confirm_comments={norm(s.format(p=p['product_name'])) for v in CONFIRM.values() for s in v for p in products}
    prohibited=forbidden|confirm_comments
    templates={
        'positive':[a+', '+b for a in INTEREST for b in CERTAIN],
        'negative':[a+b+'.' for a in QUALITY for b in REJECT],
        'neutral':[a+b for a in NEUTRAL for b in NEUTRAL_END],
        'mixed':[a+', '+b for a in INTEREST for b in HESITATE]}
    rows=list(original);seen={norm(x['content_text']) for x in rows};aug=[];confirmation=[]
    def make(label,text,product,caption,family,kind):
        state={'target_product':product['product_name'],'parent_caption':caption,'comment_text':text}
        return {'content_text':json.dumps(state,ensure_ascii=False),'interest_label':label,'family_id':family,
                'provenance':kind,'collected_at':'2026-01-26T07:00:00+07:00' if kind=='synthetic_train_augmentation' else '2026-03-31T07:00:00+07:00'}
    for label,bank in templates.items():
        for i,template in enumerate(bank):
            for product in products:
                text=template.format(p=product['product_name'])
                if norm(text) in prohibited:continue
                for caption in [f'Diskusi {product["product_name"]}. Apa ketertarikanmu?',f'{product["product_name"]} diklaim enak dan populer. Apa arah minatmu?']:
                    row=make(label,text,product,caption,f'augmentation-{label}-{i}','synthetic_train_augmentation')
                    fp=norm(row['content_text'])
                    if fp in seen:continue
                    seen.add(fp);aug.append(row)
    # CSV passed to Laya has an explicit schema; no metadata is a model input.
    train=[{'content_text':x['content_text'],'interest_label':x['interest_label']} for x in original+aug]
    for label,bank in CONFIRM.items():
        for i,template in enumerate(bank):
            for product in products:
                text=template.format(p=product['product_name'])
                assert norm(text) not in forbidden
                for caption in [f'Pembahasan {product["product_name"]}. Sampaikan minatmu.',f'Ada unggahan promosi {product["product_name"]}. Apa ketertarikanmu?']:
                    confirmation.append(make(label,text,product,caption,f'confirmation-{label}-{i}','synthetic_locked_confirmation'))
    assert not({norm(json.loads(x['content_text'])['comment_text']) for x in train}&confirm_comments)
    write(out/'train_augmented.csv',train);write(out/'augmentation_audit.csv',aug);write(out/'confirmation_locked.csv',confirmation)
    manifest={'model_task':'menu_interest','original_train_rows':len(original),'augmentation_rows':len(aug),'total_train_rows':len(train),
        'validation_rows':len(val),'legacy_test_rows':len(legacy),'confirmation_rows':len(confirmation),
        'confirmation_families':48,'target_accuracy':.95,'target_macro_f1':.95,
        'selection':'validation only; strict >0.95 accuracy AND macro F1',
        'confirmation_policy':'locked before training; evaluated once after selection; never used for selecting candidates',
        'legacy_test_status':'previously evaluated; regression set, not a fresh unbiased test',
        'provenance':'synthetic; authored template families, not independent human comments',
        'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [out/'train_augmented.csv',out/'confirmation_locked.csv',data/'train.csv',data/'validation.csv',data/'test.csv']}}
    (out/'training_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest


def notebook():
    source=Path(__file__).read_text(encoding='utf-8');runtime=(ROOT/'menu_interest_tuning.py').read_text(encoding='utf-8')
    ast.parse(source);ast.parse(runtime)
    cells=[]
    def add(kind,s):
        c={'cell_type':kind,'id':f'interest95-{len(cells):02d}','metadata':{},'source':s}
        if kind=='code':c.update(execution_count=None,outputs=[]);ast.parse(s)
        cells.append(c)
    add('markdown','# Laya ketertarikan menu: target di atas 95%\n\nFine-tuning lanjutan model ketertarikan, bukan model review produk. Target accuracy dan macro-F1 validation >95%. Kandidat dipilih hanya pada validation. Test lama dilaporkan sebagai regression set; set konfirmasi baru dikunci sebelum training dan dievaluasi sekali setelah pemilihan. Semua data sintetis, bukan bukti akurasi komentar manusia.')
    add('code',"from pathlib import Path\nimport base64,importlib.util,json,subprocess,sys,os,urllib.request,zipfile\nWORK=Path('/kaggle/working/laya_menu_interest_v2');WORK.mkdir(parents=True,exist_ok=True)\nsubprocess.run([sys.executable,'-m','pip','install','-q','laya==0.4.27'],check=True)\nDATA=None\nfor p in Path('/kaggle/input').rglob('dataset_manifest.json'):\n    m=json.loads(p.read_text())\n    if m.get('task')=='menu_interest_not_product_quality' and (p.parent/'train.csv').is_file():\n        DATA=p.parent;break\nif DATA is None:\n    source_url=globals().get('SOURCE_ARCHIVE_URL') or os.environ.get('LAYA_SOURCE_ARCHIVE_URL')\n    assert source_url,'Tambahkan output notebook sumber atau berikan URL arsip sumber dari konektor Kaggle.'\n    source_archive=WORK/'source_v1.zip'\n    urllib.request.urlretrieve(source_url,source_archive)\n    source_root=WORK/'source';source_root.mkdir(exist_ok=True)\n    with zipfile.ZipFile(source_archive) as z:\n        for entry in z.infolist():\n            dest=(source_root/entry.filename).resolve()\n            assert dest.is_relative_to(source_root.resolve())\n        z.extractall(source_root)\n    source_archive.unlink()\n    DATA=source_root/'laya_menu_interest_v1/data'\nBASE=DATA.parent/'model'\nassert (BASE/'model.safetensors').is_file(),BASE\nsource=base64.b64decode("+repr(base64.b64encode(source.encode()).decode())+").decode()\n(WORK/'prepare.py').write_text(source,encoding='utf-8')\nspec=importlib.util.spec_from_file_location('prepare',WORK/'prepare.py');prep=importlib.util.module_from_spec(spec);spec.loader.exec_module(prep)\nTRAINING=WORK/'training';manifest=prep.prepare(DATA,TRAINING)\nprint(json.dumps(manifest,indent=2))\n")
    add('markdown','## Protokol seleksi\n\nTiga konfigurasi maksimal, berhenti jika accuracy dan macro-F1 validation sama-sama >0,95. Augmentasi train memperjelas minat pasti, penolakan, preferensi/penilaian tanpa minat, serta minat disertai keraguan. Kandidat, metrik validation, hash data dan batas hasil dicatat. Set konfirmasi bukan sampel manusia independen: 48 keluarga ungkapan, diulang untuk menu/konteks berbeda.')
    add('code',"runtime=base64.b64decode("+repr(base64.b64encode(runtime.encode()).decode())+").decode()\n(WORK/'tune.py').write_text(runtime,encoding='utf-8')\nspec=importlib.util.spec_from_file_location('tune',WORK/'tune.py');tune=importlib.util.module_from_spec(spec);spec.loader.exec_module(tune)\ntune.run(WORK,DATA,TRAINING,BASE)\n")
    add('markdown','## Interpretasi\n\nTidak ada jaminan threshold tercapai pada set konfirmasi. Jika test lama tinggi setelah beberapa iterasi, itu tetap regression score. Jangan menambah data konfirmasi ke train lalu menyebutnya held-out. Tidak ada perubahan label atau penyaringan kasus salah untuk menaikkan skor. Checkpoint lama tetap ada pada notebook sumber.')
    nb={'cells':cells,'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python'}},'nbformat':4,'nbformat_minor':5}
    (ROOT/'notebooks/laya_menu_interest_tuning95.ipynb').write_text(json.dumps(nb,indent=2,ensure_ascii=False),encoding='utf-8')


if __name__=='__main__':
    print(json.dumps(prepare(ROOT/'datasets/menu_interest_v1',ROOT/'datasets/menu_interest_v2_training'),indent=2))
    notebook()
