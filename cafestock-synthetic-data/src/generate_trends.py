import numpy as np
import pandas as pd

def generate(config, tables, rng):
    start, end = pd.Timestamp(config['start_date']), pd.Timestamp(config['end_date'])
    rows = []
    # Include pre-period warm-up explicitly; never claim it was measured in NYC.
    weeks = pd.date_range(start - pd.Timedelta(days=70), end, freq='7D')
    for category in tables['categories'].category_id:
        ar = 0.
        for j, week in enumerate(weeks):
            ar = .72*ar + rng.normal(0,4)
            value = np.clip(52 + 16*np.sin(2*np.pi*(week.dayofyear/365.25 + category/8)) + ar,0,100)
            rows.append((len(rows)+1,int(category),str(week.date()),
                         week.tz_localize(config['timezone']).isoformat(),round(float(value),3),'synthetic'))
    return pd.DataFrame(rows,columns=['trend_id','category_id','week_start','available_at','interest_index','provenance'])
