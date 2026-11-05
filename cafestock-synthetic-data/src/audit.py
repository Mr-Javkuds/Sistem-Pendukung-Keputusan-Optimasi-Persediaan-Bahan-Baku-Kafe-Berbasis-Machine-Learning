"""Inspect actual source bytes; preserve observations without rewriting them."""
import csv
import hashlib
import io
import json
from pathlib import Path
import pandas as pd

REQUIRED = ['coffee-shop-sales-revenue.csv']
OPTIONAL = ['geoMap.csv','multiTimeline.csv']

def read_source(path):
    raw = path.read_bytes()
    encoding = 'utf-8-sig'
    try:
        text = raw.decode(encoding)
    except UnicodeDecodeError:
        encoding = 'cp1252'
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            encoding = 'latin-1 (lossless byte mapping; intended encoding unknown)'
            text = raw.decode('latin-1')
    lines = text.splitlines()
    skip = 2 if lines[0].startswith(('Kategori:', 'Category:')) else 0
    delimiter = csv.Sniffer().sniff('\n'.join(lines[skip:skip + 5]), delimiters=',|;\t').delimiter
    return pd.read_csv(io.StringIO(text), sep=delimiter, skiprows=skip), encoding, delimiter, skip

def audit(root):
    frames, records = {}, {}
    parts = ['# Source audit', '', 'Source observations are external evidence, not CafeStock records. '
             'Cafe reviews and all Yelp files were removed from the active project by user request. '
             'Instagram discussion is generated synthetically and is not a scraped source.', '']
    for name in REQUIRED + OPTIONAL:
        path = root / 'input' / name
        if not path.exists():
            records[name] = {'status': 'missing'}
            parts += [f'## {name}', 'MISSING. No substitute observations fabricated.', '']
            continue
        frame, encoding, sep, skip = read_source(path)
        frames[name] = frame
        rec = {'status': 'present', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
               'encoding': encoding, 'delimiter': sep, 'metadata_lines': skip,
               'rows': len(frame), 'duplicates': int(frame.duplicated().sum()),
               'columns': {c: {'dtype': str(frame[c].dtype), 'missing': int(frame[c].isna().sum()),
                               'unique': int(frame[c].nunique())} for c in frame}}
        if name.startswith('geoMap'):
            rec['format'] = 'Geographic interest by city; not a historical time series; Indonesian scope.'
        if name == 'multiTimeline.csv':
            rec['format'] = 'Weekly matcha interest, Central Java; contextual source, not Semarang city measurements.'
        for c in frame:
            if 'date' in c or c == 'Minggu':
                dates = pd.to_datetime(frame[c], errors='coerce')
                rec[c + '_range'] = [str(dates.min()), str(dates.max())]
        records[name] = rec
        parts += [f'## {name}', '```json', json.dumps(rec, indent=2, ensure_ascii=False), '```', '']
    (root / 'reports' / 'source_audit.md').write_text('\n'.join(parts), encoding='utf-8')
    (root / 'reports' / 'source_audit.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    return frames, records

if __name__ == '__main__':
    audit(Path(__file__).resolve().parents[1])
