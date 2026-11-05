"""Rule-labeled original reviews; source text is never used as a template."""
import numpy as np
import pandas as pd

def generate(config,tables,profile,rng):
    tx=tables['transactions'].set_index('transaction_id')
    products=tables['products'].set_index('product_id')
    branches=tables['branches'].set_index('branch_id')
    ratings=np.array([float(x) for x in profile['rating']])
    probs=np.array(list(profile['rating'].values()))
    reviews,aspects=[],[]
    phrases={
        'positive':['tasted fresh and balanced','was carefully prepared','had a pleasing finish','was consistently enjoyable'],
        'neutral':['was acceptable overall','met my basic expectations','was fairly ordinary','was neither exciting nor disappointing'],
        'negative':['was disappointing this time','needed more care in preparation','did not meet my expectations','had an uneven finish']}
    service={'positive':['The team was welcoming.','Service was quick and attentive.'],
             'neutral':['Service was routine.','The queue moved at an ordinary pace.'],
             'negative':['The wait felt too long.','Service felt rushed.']}
    # Source-derived nonzero aspect counts inform service-vs-product mention frequency only.
    service_rate=float(np.clip(profile['aspect_mention_rates'].get('service',.3),.1,.9))
    for item in tables['transaction_items'].itertuples():
        if item.fulfilled_qty<=0 or rng.random()>config['review_probability']:
            continue
        sale=tx.loc[item.transaction_id]
        rating=int(rng.choice(ratings,p=probs))
        label='positive' if rating>=4 else ('negative' if rating<=2 else 'neutral')
        mixed=rng.random()<.20
        label='mixed' if mixed else label
        product_label=('positive' if rating>=3 else 'negative') if mixed else label
        service_label=('negative' if product_label=='positive' else 'positive') if mixed else label
        product=products.loc[item.product_id,'product_name']
        branch=branches.loc[sale.branch_id,'branch_name']
        text=f"At CafeStock Coffee in {branch}, my {product} {rng.choice(phrases[product_label])}."
        mention_service=mixed or rng.random()<service_rate
        if mention_service:
            text+=' '+str(rng.choice(service[service_label]))
        extras=[]
        for aspect,noun in [('vibe','atmosphere'),('price','value for money'),('seating','seating')]:
            if rng.random()<profile['aspect_mention_rates'].get(aspect,.1):
                text+=f' The {noun} '+{'positive':'was pleasant.','neutral':'was ordinary.','negative':'could be improved.'}[product_label]
                extras.append(aspect)
        # Original combinatorial filler approximates a capped empirical word-length sample.
        qs=profile['review_length_quantiles']
        target=int(np.clip(rng.lognormal(np.log(max(10,qs[.5])),.65),20,180))
        fillers=['I stopped in during a short break and took time to enjoy my order.',
                 'The menu was easy to read while I considered what to choose.',
                 'I sat for a while before continuing with the rest of my day.',
                 'The visit gave me a chance to catch up with a friend nearby.',
                 'I noticed the cups and the counter while waiting for my drink.',
                 'I chose this branch because it was close to my usual route.']
        while len(text.split())<target:
            text+=' '+str(rng.choice(fillers))
        at=pd.Timestamp(sale.transaction_at)+pd.Timedelta(minutes=int(rng.integers(15,120)))
        # Same-day publication before closing; all purchases occur before 21:00 in this source.
        rid=len(reviews)+1
        reviews.append((rid,item.transaction_item_id,at.isoformat(),rating,text,label,'synthetic_rule'))
        aspects.append((len(aspects)+1,rid,'product',product_label))
        if mention_service:
            aspects.append((len(aspects)+1,rid,'service',service_label))
        for aspect in extras:
            aspects.append((len(aspects)+1,rid,aspect,product_label))
    return (pd.DataFrame(reviews,columns=['review_id','transaction_item_id','review_at','rating','review_text','sentiment_label','label_provenance']),
            pd.DataFrame(aspects,columns=['review_aspect_id','review_id','aspect','sentiment_label']))
