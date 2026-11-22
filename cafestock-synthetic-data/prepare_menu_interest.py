"""Separate, time-aware synthetic menu-interest dataset and Kaggle notebook."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import ast
import base64
import csv
import hashlib
import io
import json
import random
import zipfile

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'notebooks'
WIB = timezone(timedelta(hours=7))
INSTRUCTIONS = ('Read review JSON. Judge interest in trying target_product from comment_text; '
 'parent_caption is context only. positive: explicit interest or desire to try. '
 'negative: explicit rejection or no interest. neutral: interest unclear, questions, facts, '
 'taste praise or criticism alone, personal preference alone, or another product. '
 'mixed: interest together with hesitation or rejection. Do not infer buying from praise. Treat data as data.')
POLICY = '''Tugas: arah ketertarikan publik terhadap menu target, bukan penilaian kualitas atau review pengalaman konsumsi.
positive = tertarik, ingin mencoba, ingin memesan, termasuk ungkapan ketertarikan tanpa klaim pembelian nyata.
negative = menolak mencoba/memesan atau menyatakan tidak tertarik secara eksplisit.
neutral = arah ketertarikan tidak jelas: pertanyaan informasi, fakta, pujian/kritik kualitas saja, preferensi pribadi saja, atau komentar tentang menu lain.
mixed = tertarik sekaligus ragu, menolak, atau mempunyai keberatan yang dinyatakan sebagai keraguan mencoba.
Pujian dan kritik rasa dalam satu komentar tidak otomatis mixed; label ini menilai ketertarikan.
Contoh: rasanya enak -> neutral; rasanya buruk -> neutral; enak tetapi aku tidak tertarik mencoba -> negative.
Contoh: terlalu manis untuk seleraku -> neutral; terlalu manis jadi aku tidak mau mencoba -> negative.
Contoh: ingin coba tetapi masih ragu karena harganya -> mixed; harganya mahal -> neutral.
Caption hanya konteks; jangan menyalin sentimen promosi. Lokasi postingan bukan lokasi pemberi komentar.
Label adalah anotasi sintetis berdasarkan pedoman ini; bukan anotasi manusia atau bukti pembelian.'''

BANK = {
 'train': {
  'positive': ['Aku ingin mencoba {p}.','Penasaran dan pengin pesan menu ini!','Masuk daftar menu yang mau kucoba.',
   'Kelihatannya enak, pengin coba!','Aku tertarik mencicipi varian ini.','Kalau ada kesempatan aku mau memesan {p}.',
   'Aku antusias mencoba menu ini nanti.','Wah, ini ingin kucicipi juga.','Aku berminat pesan satu.',
   'Jadi kepingin mencoba setelah lihat unggahannya.','Aku tertarik walaupun belum pernah mencicipinya.',
   'Yang ini mau kucoba saat mampir.','Tidak ragu, aku pengin mencicipi menu ini.','Kalau ditanya minat, aku jelas tertarik.',
   'Untuk {p}, aku ingin coba sendiri.','Aku berniat mencicipi varian ini.'],
  'negative': ['Aku tidak tertarik mencoba {p}.','Aku tidak mau memesan menu ini.','Bukan menu yang ingin kucoba.',
   'Aku memilih melewatkan varian ini, tidak berminat.','Tidak ada niat mencoba yang ini.','Aku menolak mencicipi menu ini.',
   'Kelihatan enak, tetapi aku tidak ingin mencobanya.','Rasanya katanya bagus, aku tetap tidak berminat pesan.',
   'Terlalu manis jadi aku tidak mau mencoba.','Aku tidak akan memilih {p}, memang tidak tertarik.',
   'Aku nggak kepengin nyobain ini.','Aku memutuskan tidak mencoba varian ini.',
   'Meski tampilannya cantik, aku tidak minat mencicipi.','Buat aku lewat dulu, aku tidak ingin mencoba.',
   'Aku tidak berminat sama menu yang dibahas ini.','Aku memilih tidak memesan karena tidak tertarik.'],
  'neutral': ['Rasanya enak.','Cuma menang tampilan, rasanya mengecewakan.','Terlalu manis untuk seleraku.',
   'Itu topping di atasnya apa?','Harga satu porsi berapa?','Aku belum punya pendapat tentang ketertarikanku.',
   'Aromanya wangi tetapi rasanya terlalu pahit.','Harganya mahal.','Ini menggunakan susu jenis apa?',
   'Aku pribadi lebih suka rasa kurang manis.','Menu ini tersedia mulai jam berapa?',
   'Aku bilang kualitasnya bagus, bukan menyatakan ingin mencoba.','Produknya terlihat buruk kualitasnya.',
   'Ada kandungan kacang dalam menu ini?','Aku masih mencari informasi, belum menyatakan minat.',
   'Aku ingin mencoba menu lain, bukan membahas minat terhadap yang ini.'],
  'mixed': ['Aku ingin mencoba, tetapi masih ragu karena harganya.','Tertarik sih, tapi sekaligus enggan mencobanya.',
   'Pengin pesan, namun aku bimbang dengan porsinya.','Aku penasaran ingin mencicipi, tapi takut tidak cocok.',
   'Aku berminat mencoba {p}, cuma masih ragu.','Sebagian diriku ingin coba, sebagian lagi menolak.',
   'Aku ingin mencicipi tetapi belum yakin akan memilihnya.','Mau pesan menu ini, tapi ragu soal kemanisannya.',
   'Ada minat mencoba, namun ada rasa enggan juga.','Aku pengin coba sekaligus masih khawatir dengan rasanya.',
   'Tertarik memesan, tapi keberatan harga bikin aku bimbang.','Ingin sih, namun aku masih ragu untuk mencoba.',
   'Aku mau mencicipi, hanya saja ada keraguan dengan bahannya.','Aku tertarik tetapi juga ingin menghindarinya.',
   'Minat mencoba ada, tapi aku belum yakin menu ini cocok.','Aku ingin pesan {p}, tapi ragu setelah membaca deskripsinya.']},
 'validation': {
  'positive': ['Aku memasukkan menu ini ke wishlist untuk dicicipi.','Ada keinginan kuat buat nyobain yang ini.',
   'Aku berminat menikmati {p} saat berkunjung.','Yang ini membuatku ingin order.',
   'Aku ingin tahu rasanya dengan mencobanya sendiri.','Aku naksir menu ini dan mau mencicipi.'],
  'negative': ['Aku ogah mencicipi varian ini.','Tidak ada ketertarikan untuk memesan yang ini.',
   'Aku tidak kepikiran mencoba karena memang tidak minat.','Bagus tampilannya, tapi aku menolak mencobanya.',
   'Aku tidak ingin memilih menu ini untuk kucoba.','Menu ini tidak membangkitkan keinginanku mencoba.'],
  'neutral': ['Boleh tahu isian {p} apa saja?','Enak dan wangi menurut penilaianku.',
   'Rasanya hambar dan kualitasnya buruk.','Kalau seleraku biasanya pilih yang lebih ringan.',
   'Bahan produknya dari apa, ya?','Pujian rasa ini bukan pernyataan minat untuk mencoba.'],
  'mixed': ['Aku mau mencicipi, namun masih bimbang melihat harganya.','Penasaran untuk coba tetapi aku juga enggan.',
   'Aku berminat order, meski masih meragukan kecocokannya.','Aku ingin coba sambil tetap merasa ragu.',
   'Menu ini menarik minatku, tetapi aku belum yakin mau mencicipi.','Pengin menikmati {p}, cuma keraguan belum hilang.']},
 'test': {
  'positive': ['Aku sudah niat buat nyicip menu yang ditampilkan ini.','Aku pengin merasakan {p} sendiri!',
   'Ada ketertarikan untuk nyobain varian tersebut.','Menu ini bakal masuk daftar coba pribadiku.',
   'Aku ingin memesan ini kalau berkesempatan.','Aku tertarik, mau cicip satu porsi.'],
  'negative': ['Aku sama sekali nggak berminat nyicip yang di foto.','Aku tidak mempunyai keinginan memesan {p}.',
   'Meskipun katanya nikmat, aku ogah mencoba.','Aku menghindari mencoba varian ini karena tidak minat.',
   'Yang ini tidak akan kupilih untuk dicicipi.','Aku memilih skip dan tidak tertarik order.'],
  'neutral': ['Berapa ukuran sajian yang diunggah ini?','Menurutku rasanya sedap dan penyajiannya cantik.',
   'Kualitasnya mengecewakan, cuma penilaian rasa dariku.','Buat lidahku kemanisannya berlebihan.',
   'Apakah topping tersebut mengandung alergen?','Bisa dijelaskan komposisinya dulu?'],
  'mixed': ['Mau nyobain, tetapi keraguan soal harga masih ada.','Aku ingin memesan namun belum yakin akan cocok.',
   'Aku punya keinginan mencicipi sekaligus rasa enggan.','Minatku ada, tapi aku masih sangsi dengan menu ini.',
   'Pengen merasakan {p}, namun kekhawatiranku belum reda.','Aku tertarik mencoba walaupun masih bimbang memilih.']},
 'forecast': {
  'positive': ['Aku tertarik menikmati menu ini minggu depan.','Aku ingin ikut mencicipi varian ini.','Aku mau coba satu porsi {p}.',
   'Menu ini bikin aku pengin pesan untuk dicoba.','Aku berminat mencicipinya saat ada kesempatan.','Aku ingin merasakan menu yang ini.'],
  'negative': ['Aku tidak berminat untuk ikut mencoba.','Aku menolak pesan {p} untuk dicicipi.','Aku memilih tidak mencoba menu yang ini.',
   'Meski dipuji orang, aku tidak tertarik memesan.','Aku enggan mencoba karena memang tidak minat.','Aku tidak mempunyai niat mencicipinya.'],
  'neutral': ['Rasanya bagus tetapi harganya tinggi.','Menurutku kualitas rasanya kurang baik.','Ini topping-nya terbuat dari bahan apa?',
   'Untuk preferensiku ini kemanisan.','Aku belum menyatakan tertarik atau tidak.','Jam berapa menu ini tersedia?'],
  'mixed': ['Aku ingin ikut mencoba tetapi masih ragu dengan harganya.','Aku tertarik memesan, namun juga enggan mencicipinya.',
   'Ada keinginan mencoba yang ini sekaligus kekhawatiran.','Aku mau coba {p}, tapi tetap bimbang.',
   'Pengin merasakan, tetapi aku belum yakin menu ini cocok.','Aku berminat mencoba sambil masih meragukan pilihan itu.']}}


def iso(t): return t.isoformat()


def phase(at):
    if at < datetime(2026,2,1,tzinfo=WIB): return 'train'
    if at < datetime(2026,3,1,tzinfo=WIB): return 'validation'
    if at < datetime(2026,4,1,tzinfo=WIB): return 'test'
    return 'forecast' if at <= datetime(2026,11,3,23,59,tzinfo=WIB) else 'pending'


def read(name):
    with (ROOT/'output'/f'{name}.csv').open(encoding='utf-8',newline='') as f: return list(csv.DictReader(f))


def build(emit_notebook=True):
    rng=random.Random(20261108)
    products=read('products'); posts=[]; comments=[]; first={}; groups={p:[] for p in BANK}
    start=datetime(2025,11,3,tzinfo=WIB)
    for w in range(53):
        monday=start+timedelta(weeks=w)
        collected=monday+timedelta(days=7,hours=7)
        split=phase(collected); bank_split='forecast' if split=='pending' else split
        for region in [1,2,3,4,None]:
            for product in products:
                # Occasional second source makes post dominance auditable.
                for source in range(2 if w%6==0 else 1):
                    published=monday+timedelta(days=1+source,hours=12)
                    if published>datetime(2026,11,3,23,59,tzinfo=WIB): continue
                    post_id=f'INT-{w:02}-{region or 0}-{product["product_id"]}-{source}'
                    caption=(f'Diskusi menu {product["product_name"]}. '
                             +('Katanya enak dan sedang viral, bagaimana ketertarikan kalian?' if source==0 else 'Apa arah ketertarikan kalian terhadap menu ini?'))
                    posts.append({'post_id':post_id,'product_id':product['product_id'],'target_product':product['product_name'],
                        'parent_caption':caption,'post_location_region_id':region or '', 'location_provenance':'synthetic_post_tag' if region else 'unknown',
                        'commenter_location_known':False,'published_at':iso(published),'collected_at':iso(collected),
                        'split':split,'provenance':'synthetic_interest_scenario'})
                    # Label mix is independent per source; does not use future demand.
                    weights=[rng.gammavariate(1.4,1) for _ in range(4)]
                    n=40 if source==1 else rng.choice([4,6,8])
                    for j in range(n):
                        label=rng.choices(list(BANK[bank_split]),weights=weights,k=1)[0]
                        phrases=BANK[bank_split][label]; family=rng.randrange(len(phrases))
                        text=phrases[family].format(p=product['product_name'])
                        state={'target_product':product['product_name'],'parent_caption':caption,'comment_text':text}
                        content=json.dumps(state,ensure_ascii=False)
                        fp=hashlib.sha256(content.casefold().encode()).hexdigest()
                        eligible=fp not in first
                        first.setdefault(fp,post_id)
                        row={'comment_id':f'{post_id}-C{j:02}','post_id':post_id,'product_id':product['product_id'],
                            'content_text':content,'comment_text':text,'interest_label':label,
                            'comment_published_at':iso(published+timedelta(minutes=10+j)),
                            'collected_at':iso(collected),'post_location_region_id':region or '',
                            'commenter_location_region_id':'','family_id':f'{bank_split}-{label}-{family}',
                            'split':split,'training_status':'eligible' if eligible else 'duplicate_text',
                            'label_provenance':'synthetic_interest_rule'}
                        comments.append(row)
                        if eligible and split in groups: groups[split].append(row)
    # Data contract checks before packaging.
    assert all(c['comment_published_at']<c['collected_at'] for c in comments)
    for a,b in [('train','validation'),('train','test'),('validation','test')]:
        assert not(set(x['family_id'] for x in groups[a]) & set(x['family_id'] for x in groups[b]))
        assert max(x['collected_at'] for x in groups[a])<min(x['collected_at'] for x in groups[b])
    bio=io.BytesIO()
    with zipfile.ZipFile(bio,'w',zipfile.ZIP_DEFLATED) as z:
        def put_csv(name,rows):
            s=io.StringIO(newline=''); writer=csv.DictWriter(s,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows);z.writestr(name,s.getvalue())
        put_csv('posts.csv',posts);put_csv('comments.csv',comments)
        for p in ['train','validation','test']: put_csv(p+'.csv',groups[p])
        for name in ['products','branches','recipes','recipe_ingredients','ingredients']: put_csv(name+'.csv',read(name))
        z.writestr('instructions.txt',INSTRUCTIONS);z.writestr('label_policy.txt',POLICY)
        manifest={'task':'menu_interest_not_product_quality','seed':20261108,'provenance':'synthetic',
            'raw_posts':len(posts),'raw_comments':len(comments),'nlp_eligible_counts':{k:len(v) for k,v in groups.items()},
            'nlp_split_by':'collected_at; all post comments stay together; dedup training texts',
            'nlp_model_available_at':'2026-04-01T00:00:00+07:00','forecast_start':'2026-04-07T05:00:00+07:00',
            'source_cap_comments':5,'post_weight':'equal after cap; each post <= 1 unit of weight',
            'location_limit':'post tag is context; commenter location unknown','not_real_market_data':True}
        z.writestr('dataset_manifest.json',json.dumps(manifest,indent=2))
    OUT.mkdir(exist_ok=True)
    blob=bio.getvalue(); (OUT/'laya_menu_interest_data.zip').write_bytes(blob)
    if not emit_notebook:
        print(json.dumps(manifest,indent=2))
        return
    script=(ROOT/'menu_interest_experiment.py').read_text(encoding='utf-8')
    ast.parse(script)
    cells=[]
    def add(kind,text):
        c={'cell_type':kind,'id':f'menu-interest-{len(cells):02d}','metadata':{},'source':text}
        if kind=='code':c.update(execution_count=None,outputs=[]);ast.parse(text)
        cells.append(c)
    add('markdown','# Laya: Ketertarikan Publik terhadap Menu\n\nEksperimen baru, terpisah dari review produk dan sentimen kualitas. Data sintetis baru; label mengukur ketertarikan, bukan pembelian.\n\n'+POLICY)
    add('markdown','## Desain waktu dan sumber\n\nNLP train Nov–Jan, validation Februari, test Maret berdasarkan collected_at. Checkpoint baru dianggap tersedia 1 April; peramalan dimulai 7 April. Data satu postingan tidak dibagi antar-partisi. Maksimal lima komentar per postingan, lalu bobot postingan disetarakan. Tag lokasi adalah konteks postingan, bukan lokasi pemberi komentar.\n\nTiga hipotesis simulator: hubungan ketertarikan–permintaan kuat, lemah, nol. RF Regressor A–D diuji dengan MAE/RMSE per bahan. Ini tidak mengukur laba atau penghematan biaya.')
    tables={name:(ROOT/'output'/f'{name}.csv').read_text(encoding='utf-8') for name in ['products','branches','recipes','recipe_ingredients','ingredients']}
    builder_source=Path(__file__).read_text(encoding='utf-8')
    add('code',"from pathlib import Path\nimport base64,zipfile,io,subprocess,sys,importlib.util\nWORK=Path('/kaggle/working/laya_menu_interest_v1');WORK.mkdir(parents=True,exist_ok=True)\nDATA=WORK/'data';DATA.mkdir(exist_ok=True)\n(WORK/'output').mkdir(exist_ok=True)\ntables="+repr(tables)+"\nfor name,text in tables.items():\n    (WORK/'output'/(name+'.csv')).write_text(text,encoding='utf-8')\nbuilder_source=base64.b64decode("+repr(base64.b64encode(builder_source.encode()).decode())+").decode()\n(WORK/'prepare_menu_interest.py').write_text(builder_source,encoding='utf-8')\nspec=importlib.util.spec_from_file_location('data_builder',WORK/'prepare_menu_interest.py')\nbuilder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)\nbuilder.build(emit_notebook=False)\nwith zipfile.ZipFile(WORK/'notebooks/laya_menu_interest_data.zip') as z:\n    for n in z.namelist():\n        assert '/' not in n and '\\\\' not in n\n        (DATA/n).write_bytes(z.read(n))\nscript=base64.b64decode("+repr(base64.b64encode(script.encode()).decode())+").decode()\n(WORK/'experiment.py').write_text(script,encoding='utf-8')\nsubprocess.run([sys.executable,'-m','pip','install','-q','laya==0.4.27'],check=True)\n")
    add('markdown','## Training dan evaluasi\n\nModel dimulai dari Laya multilingual dasar. Validation untuk pemantauan; test tidak diberikan kepada training. Kata sifat enak/buruk saja masuk neutral bila tidak menyatakan minat. Prediksi Laya dipakai pada fitur C/D; label referensi hanya dipakai simulator untuk mendefinisikan hipotesis yang diuji. Test sintetis belum menggantikan anotasi komentar nyata.')
    add('code',"import importlib.util\nspec=importlib.util.spec_from_file_location('interest_experiment',WORK/'experiment.py')\nexperiment=importlib.util.module_from_spec(spec);spec.loader.exec_module(experiment)\nexperiment.run(WORK,DATA)\n")
    add('markdown','## Output\n\nCheckpoint Laya baru, prediksi NLP, challenge aturan, sinyal berbobot per produk/wilayah/minggu, prediksi RF A–D per skenario, MAE/RMSE per bahan, manifest dan audit waktu/sumber. Model lama dan pipeline produksi tidak diganti. Data ini hanya simulasi hubungan yang dinyatakan, bukan bukti niat membeli atau permintaan lokal nyata.')
    nb={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'}},'nbformat':4,'nbformat_minor':5}
    (OUT/'laya_menu_interest_kaggle.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(manifest,indent=2)); print('Notebook syntax validated.')


if __name__=='__main__': build()
