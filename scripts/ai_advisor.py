import os,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; key=os.getenv('OPENAI_API_KEY')
if not key: print('No OPENAI_API_KEY; deterministic brief kept.'); raise SystemExit(0)
from openai import OpenAI
d=json.loads((ROOT/'data.json').read_text()); compact={'business':d['business'],'window':d['window'],'metrics':d['metrics'],'alerts':d['alerts'][:5],'categories':sorted(d['category_stats'],key=lambda x:x['negative_mentions'],reverse=True)[:7],'menu':d['menu_stats'][:7]}
prompt='You are a restaurant operations analyst. Using ONLY this JSON evidence, write a concise owner brief: overall health, 3 findings, 3 actions, and what to monitor next. Do not invent causes.\n'+json.dumps(compact)
resp=OpenAI(api_key=key).responses.create(model=os.getenv('OPENAI_MODEL','gpt-5-mini'),input=prompt); d['ai_owner_brief']=resp.output_text; (ROOT/'data.json').write_text(json.dumps(d,indent=2)); print('AI brief added')
