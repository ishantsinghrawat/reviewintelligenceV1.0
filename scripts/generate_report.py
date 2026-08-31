import json
from pathlib import Path
from datetime import date
ROOT=Path(__file__).resolve().parents[1]; d=json.loads((ROOT/'data.json').read_text()); m=d['metrics']; b=d['brief']
lines=['# Weekly Restaurant Customer Intelligence','',f"**{d['business']['name']} — {d['business']['location']}**",f"Window: {d['window']['start']} to {d['window']['end']}",'',f"- Reviews: **{m['reviews']}**",f"- Average rating: **{m['average_rating']} / 5**",f"- Positive: **{m['positive_pct']}%**",f"- Negative: **{m['negative_pct']}%**",f"- Active alerts: **{m['alerts']}**",'',f"## {b['headline']}",b['summary'],'','## Top concerns']+[f'- {x}' for x in b['top_concerns']]+['','## Top strengths']+[f'- {x}' for x in b['top_strengths']]+['','## Recommended actions']+[f'- {x}' for x in b['recommended_actions']]
text='\n'.join(lines); (ROOT/'weekly_report.md').write_text(text); (ROOT/'reports'/f'{date.today().isoformat()}.md').write_text(text); print('Generated weekly report')
