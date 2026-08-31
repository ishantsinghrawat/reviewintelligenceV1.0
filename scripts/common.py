from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
def load_json(p): return json.loads(Path(p).read_text())
def save_json(p,o): Path(p).write_text(json.dumps(o,indent=2,ensure_ascii=False))
def review_id(r):
    if r.get("review_id"): return r["review_id"]
    raw="|".join(str(r.get(k,"")) for k in ("source","business","location","review_date","author","review"))
    return hashlib.sha256(raw.encode()).hexdigest()[:20]
def sentiment_from_rating(x):
    x=int(float(x or 3)); return "Positive" if x>=4 else "Negative" if x<=2 else "Neutral"
def confidence_band(s): return "High" if s>=.75 else "Medium" if s>=.5 else "Low"
