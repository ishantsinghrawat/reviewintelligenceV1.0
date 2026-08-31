"""Quick public demo connector. Google Places returns at most 5 reviews for a place."""
import os,requests,csv
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parents[1]
key=os.getenv('GOOGLE_MAPS_API_KEY'); pid=os.getenv('GOOGLE_PLACE_ID')
if not key or not pid: raise SystemExit('Set GOOGLE_MAPS_API_KEY and GOOGLE_PLACE_ID')
r=requests.get(f'https://places.googleapis.com/v1/places/{pid}',headers={'X-Goog-Api-Key':key,'X-Goog-FieldMask':'id,displayName,rating,userRatingCount,reviews'},timeout=30); r.raise_for_status(); p=r.json(); rows=[]
for i,x in enumerate(p.get('reviews',[]),1):
    rows.append({'review_id':f'places-{pid}-{i}','business':(p.get('displayName') or {}).get('text',''),'location':'','review_date':(x.get('publishTime') or datetime.utcnow().isoformat())[:10],'rating':x.get('rating',3),'review':((x.get('text') or {}).get('text') or ''),'source':'Google Places','author':((x.get('authorAttribution') or {}).get('displayName') or 'Google reviewer')})
if not rows: raise SystemExit('No reviews returned')
with open(ROOT/'data/reviews.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=rows[0]); w.writeheader(); w.writerows(rows)
print(f'Wrote {len(rows)} reviews')
