"""Deterministic text eligibility without fitting on validation/test data."""
import hashlib
import re
import unicodedata

def text_fingerprint(text):
    canonical=re.sub(r'\s+',' ',unicodedata.normalize('NFKC',str(text)).casefold()).strip()
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

def mark_sentiment_eligibility(frame):
    """Keep earliest collected text; never relocate later observations into train.

    Repeated posts remain in raw/relational tables. Only ML eligibility changes.
    Pending batches are never admitted and cannot disqualify any earlier record.
    """
    result=frame.copy()
    result['text_fingerprint']=result.content_text.map(text_fingerprint)
    status={}; seen={}
    ordered=result.sort_values(['collected_at','post_id','mention_id'],kind='stable')
    for row in ordered.itertuples():
        if row.split=='pending':
            status[row.Index]='pending'; continue
        if row.text_fingerprint in seen:
            status[row.Index]='duplicate' if seen[row.text_fingerprint]==row.sentiment_label else 'label_conflict'
        else:
            seen[row.text_fingerprint]=row.sentiment_label
            status[row.Index]='eligible'
    result['training_status']=result.index.map(status)
    return result
