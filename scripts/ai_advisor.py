import os,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
key=os.getenv('OPENAI_API_KEY')
if not key:
    print('No OPENAI_API_KEY; V2 deterministic insights and contextual responses kept.')
    raise SystemExit(0)
from openai import OpenAI

d=json.loads((ROOT/'data.json').read_text(encoding='utf-8'))
compact={
    'business':d['business'],
    'window':d['window'],
    'metrics':d['metrics'],
    'priority_issues':d.get('priority_issues',[])[:3],
    'patterns':d.get('patterns',[])[:4],
    'menu':d.get('menu_stats',[])[:8],
    'reviews_needing_response':[
        {'review_id':x['review_id'],'rating':x['rating'],'review':x['review'],'negative_aspects':x.get('negative_aspects',[]),'positive_aspects':x.get('positive_aspects',[]),'menu_items':x.get('menu_items',[])}
        for x in d.get('response_drafts',[])[:30]
    ]
}
requirements="""You are a restaurant operations and customer-response assistant. Use ONLY the supplied JSON evidence.
Return VALID JSON only with this exact shape:
{"owner_brief":"one concise paragraph","responses":[{"review_id":"...","draft_response":"..."}]}

Owner brief:
- explain meaningful operational findings, not just counts
- connect issues only when the evidence supports it
- give 2-3 practical actions
- do not invent causes, staffing facts, times or business facts

Responses:
- 45-90 words each
- natural and non-repetitive
- acknowledge specific positive feedback when present
- address actual negative aspects
- never invent facts, refunds, compensation, contact details or promises
- do not admit legal liability
- avoid robotic wording such as 'your experience with wait time'

Evidence JSON:
"""
prompt=requirements+json.dumps(compact,ensure_ascii=False)
model=os.getenv('OPENAI_MODEL') or 'gpt-5.6-luna'
resp=OpenAI(api_key=key).responses.create(model=model,input=prompt)
raw=resp.output_text.strip()
raw=re.sub(r'^```(?:json)?\s*|\s*```$','',raw,flags=re.I|re.S)
try:
    result=json.loads(raw)
except Exception as e:
    print('AI output was not valid JSON; deterministic V2 output kept:',e)
    raise SystemExit(0)
if result.get('owner_brief'):
    d['ai_owner_brief']=result['owner_brief']
byid={x.get('review_id'):x.get('draft_response') for x in result.get('responses',[]) if x.get('review_id') and x.get('draft_response')}
for x in d.get('response_drafts',[]):
    if x['review_id'] in byid:
        x['draft_response']=byid[x['review_id']]
        x['response_mode']='AI personalized'
(ROOT/'data.json').write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8')
(ROOT/'response_drafts.json').write_text(json.dumps(d.get('response_drafts',[]),indent=2,ensure_ascii=False),encoding='utf-8')
print(f"AI owner brief + {sum(1 for x in d.get('response_drafts',[]) if x.get('response_mode')=='AI personalized')} personalized responses added using {model}.")
