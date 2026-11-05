"""Original Indonesian Instagram-like menu discussion, never actual Instagram records."""
import numpy as np
import pandas as pd

LABELS=['positive','neutral','negative','mixed']
PROBABILITIES=[.45,.20,.20,.15]
POSITIVE=['rasanya enak dan seimbang','teksturnya lembut dan nyaman dinikmati',
          'aromanya menarik dan bikin ingin mencoba lagi','rasanya cocok untuk seleraku']
NEGATIVE=['rasanya kurang seimbang','terlalu manis untuk seleraku',
          'rasanya kurang cocok di lidahku','teksturnya terasa kurang pas']
NEUTRAL=['sedang sering muncul di linimasaku','masuk daftar menu yang ingin aku cari tahu',
         'sedang aku bandingkan dengan menu lain','jadi topik obrolan sore ini']
VALUE={'positive':'Menurutku porsi dan rasanya sepadan.',
       'neutral':'Untuk harga aku belum punya kesimpulan.',
       'negative':'Untuk porsi seperti itu, harganya terasa mahal.'}

def monthly_collection(published,tz):
    local=pd.Timestamp(published).tz_convert(tz)
    return (pd.Timestamp(local.date()).to_period('M').to_timestamp()+pd.offsets.MonthBegin(1)
            +pd.Timedelta(hours=7)).tz_localize(tz)

def generate(config,tables,rng):
    posts=[]; mentions=[]; aspects=[]
    regions=tables['regions'].set_index('region_id')
    products=tables['products'].set_index('product_id')
    openers=['Lagi bahas','Obrolan menu hari ini:','Menurut seleraku,','Pilihan minuman dan camilan:']
    closers=['Selera orang bisa beda-beda.','Ada yang suka menu seperti ini juga?',
             'Cocok jadi bahan diskusi menu minggu ini.','Ini pendapat soal menunya, bukan tempatnya.']
    for day in pd.date_range(config['start_date'],config['end_date']):
        for _ in range(rng.poisson(config['mean_daily_social_posts'])):
            pid=int(rng.choice(products.index))
            region=int(rng.choice([0,1,2,3,4],p=[.05,.35,.20,.20,.20]))
            label=str(rng.choice(LABELS,p=PROBABILITIES))
            taste='positive' if label=='mixed' else label
            value='negative' if label=='mixed' else label
            phrase=rng.choice(POSITIVE if taste=='positive' else NEGATIVE if taste=='negative' else NEUTRAL)
            location=regions.loc[region,'region_name'] if region else 'lokasi belum disebutkan'
            text=f'{rng.choice(openers)} {products.loc[pid,"product_name"]}: {phrase}. {VALUE[value]} '
            text+=f'Bahasan wilayah {location}. {rng.choice(closers)} #bahasmenu'
            if region: text+=' #Semarang'
            published=(day+pd.Timedelta(hours=int(rng.integers(8,23)),minutes=int(rng.integers(60)))).tz_localize(config['timezone'])
            collected=monthly_collection(published,config['timezone'])
            postid=len(posts)+1; mentionid=len(mentions)+1
            posts.append((postid,'instagram',f'SIM-IG-SMG-{postid:07d}',None,text,
                          published.isoformat(),collected.isoformat(),collected.strftime('BATCH-%Y%m'),
                          region or None,'synthetic_scenario' if region else 'unknown','id','synthetic'))
            mentions.append((mentionid,postid,pid,label,'synthetic_rule'))
            aspects.append((len(aspects)+1,mentionid,'taste',taste))
            aspects.append((len(aspects)+1,mentionid,'value',value))
    return {
        'social_posts':pd.DataFrame(posts,columns=['post_id','platform','source_post_key','source_url','content_text',
            'published_at','collected_at','batch_key','region_id','location_evidence','language','provenance']),
        'menu_mentions':pd.DataFrame(mentions,columns=['mention_id','post_id','product_id','sentiment_label','label_provenance']),
        'menu_aspects':pd.DataFrame(aspects,columns=['menu_aspect_id','mention_id','aspect','sentiment_label'])}

def aggregate(tables):
    data=tables['menu_mentions'].merge(tables['social_posts'],on='post_id')
    data=data[data.region_id.notna()].copy()
    data['period_start']=data.published_at.str[:7]+'-01'
    rows=[]
    for (region,product,period),g in data.groupby(['region_id','product_id','period_start'],sort=True):
        counts=g.sentiment_label.value_counts()
        score=g.sentiment_label.map({'positive':1,'negative':-1,'neutral':0,'mixed':0}).mean()
        rows.append((len(rows)+1,int(region),int(product),period,g.collected_at.max(),
                     g.published_at.max(),g.post_id.nunique(),*[int(counts.get(k,0)) for k in LABELS],float(score),'synthetic'))
    return pd.DataFrame(rows,columns=['signal_id','region_id','product_id','period_start','available_at',
        'source_max_published_at','post_count','positive_count','neutral_count','negative_count','mixed_count',
        'sentiment_mean','provenance'])
