from __future__ import annotations
import csv, re
from collections import defaultdict
from datetime import datetime, timedelta
from common import ROOT, load_json, save_json, review_id, sentiment_from_rating

POSITIVE={"amazing","awesome","best","delicious","excellent","fantastic","fresh","friendly","good","great","helpful","love","loved","nice","perfect","quick","tasty","wonderful"}
NEGATIVE={"awful","bad","bland","cold","dirty","disappointing","expensive","late","missing","overpriced","poor","rude","slow","stale","terrible","unacceptable","wrong","worst"}

def norm(s): return (s or '').lower().strip()
def split_sentences(text): return [p.strip() for p in re.split(r'(?<=[.!?])\\s+|[;\\n]+', text or '') if p.strip()]

def local_sentiment(text,rating=3):
    toks=re.findall(r"[a-zA-Z']+",norm(text)); pos=sum(t in POSITIVE for t in toks); neg=sum(t in NEGATIVE for t in toks)
    if pos>neg: return 'Positive',min(.95,.58+.08*(pos-neg))
    if neg>pos: return 'Negative',min(.95,.58+.08*(neg-pos))
    return sentiment_from_rating(rating),.48

def classify_aspects(text,taxonomy,rating):
    out={}; sentences=split_sentences(text)
    for cat,kws in taxonomy['keywords'].items():
        matches=[]; hits=[]
        for s in sentences:
            sh=[kw for kw in kws if kw in norm(s)]
            if sh: matches.append(s); hits.extend(sh)
        if matches:
            sent,conf=local_sentiment(' '.join(matches),rating)
            out[cat]={'category':cat,'score':round(min(.97,.60+.06*len(set(hits))),3),'sentiment':sent,'sentiment_confidence':round(conf,3),'hits':sorted(set(hits))[:6]}
    if not out:
        out['Food Quality']={'category':'Food Quality','score':.40,'sentiment':sentiment_from_rating(rating),'sentiment_confidence':.40,'hits':[]}
    return sorted(out.values(),key=lambda x:x['score'],reverse=True)

def find_menu(text,items):
    t=norm(text); return [x for x in items if x.lower() in t]

def load_reviews():
    real=ROOT/'data/reviews.csv'; sample=ROOT/'data/sample_reviews.csv'; p=real if real.exists() else sample
    with open(p,encoding='utf-8') as f: rows=list(csv.DictReader(f))
    return rows,p.name,('real' if real.exists() else 'demo')

def pct(n,d): return round(100*n/d,1) if d else 0

def rollup(items,categories):
    s={c:{'mentions':0,'positive':0,'neutral':0,'negative':0} for c in categories}
    for r in items:
        for a in r['aspects']:
            x=s[a['category']]; x['mentions']+=1; x[a['sentiment'].lower()]+=1
    return s

def run():
    tax=load_json(ROOT/'config/taxonomy.json'); settings=load_json(ROOT/'config/settings.json'); raw,source_file,data_mode=load_reviews()
    enriched=[]
    for r in raw:
        try: rating=int(float(r.get('rating') or 3))
        except: rating=3
        aspects=classify_aspects(r.get('review',''),tax,rating)
        enriched.append({**r,'review_id':review_id(r),'rating':rating,'sentiment':sentiment_from_rating(rating),'primary_category':aspects[0]['category'],'aspects':aspects,'menu_items':find_menu(r.get('review',''),tax['menu_items']),'review_reply_url':r.get('review_reply_url') or ''})
    enriched.sort(key=lambda x:x.get('review_date',''),reverse=True)
    if not enriched: raise SystemExit('No reviews found.')
    latest=max(datetime.fromisoformat(r['review_date']).date() for r in enriched)
    cur_start=latest-timedelta(days=29); prev_start=latest-timedelta(days=59)
    cur=[r for r in enriched if datetime.fromisoformat(r['review_date']).date()>=cur_start]
    prev=[r for r in enriched if prev_start<=datetime.fromisoformat(r['review_date']).date()<cur_start]
    cr,pr=rollup(cur,tax['categories']),rollup(prev,tax['categories'])
    category_stats=[]
    for c in tax['categories']:
        a,b=cr[c],pr[c]
        category_stats.append({'category':c,**a,'negative_rate':round(a['negative']/a['mentions'],3) if a['mentions'] else 0,'positive_rate':round(a['positive']/a['mentions'],3) if a['mentions'] else 0,'prior_mentions':b['mentions'],'prior_negative':b['negative'],'negative_change':a['negative']-b['negative']})

    l7s=latest-timedelta(days=6); p7s=latest-timedelta(days=13)
    l7=[r for r in enriched if datetime.fromisoformat(r['review_date']).date()>=l7s]
    p7=[r for r in enriched if p7s<=datetime.fromisoformat(r['review_date']).date()<l7s]
    lr,pr7=rollup(l7,tax['categories']),rollup(p7,tax['categories'])
    alerts=[]; min_m=settings.get('alert',{}).get('min_mentions',4); ratio_min=settings.get('alert',{}).get('increase_ratio',1.5)
    for c in tax['categories']:
        now,before=lr[c]['negative'],pr7[c]['negative']; ratio=(now/before) if before else (999 if now else 0)
        if now>=min_m and ratio>=ratio_min:
            alerts.append({'category':c,'current_negative':now,'previous_negative':before,'increase_ratio':None if ratio==999 else round(ratio,2),'severity':'High' if now>=8 or ratio>=2 else 'Medium','window':'latest 7 days vs prior 7 days'})

    trend=defaultdict(lambda:{'reviews':0,'rating_total':0,'positive':0,'negative':0})
    for r in enriched:
        m=r['review_date'][:7]; t=trend[m]; t['reviews']+=1; t['rating_total']+=r['rating']; t['positive']+=r['sentiment']=='Positive'; t['negative']+=r['sentiment']=='Negative'
    monthly=[{'month':m,'reviews':t['reviews'],'average_rating':round(t['rating_total']/t['reviews'],2),'positive_pct':pct(t['positive'],t['reviews']),'negative_pct':pct(t['negative'],t['reviews'])} for m,t in sorted(trend.items())]

    menu=[]
    for item in tax['menu_items']:
        rr=[r for r in cur if item in r['menu_items']]
        if not rr: continue
        pos=neg=neu=0
        for r in rr:
            relevant=' '.join(s for s in split_sentences(r['review']) if item.lower() in norm(s)); sent,_=local_sentiment(relevant or r['review'],r['rating'])
            pos+=sent=='Positive'; neg+=sent=='Negative'; neu+=sent=='Neutral'
        menu.append({'item':item,'mentions':len(rr),'positive':pos,'negative':neg,'neutral':neu,'positive_pct':pct(pos,len(rr)),'negative_pct':pct(neg,len(rr)),'avg_rating':round(sum(r['rating'] for r in rr)/len(rr),2)})
    menu.sort(key=lambda x:(x['mentions'],x['positive_pct']),reverse=True)

    ratings=[r['rating'] for r in cur]; avg=round(sum(ratings)/len(ratings),2) if ratings else 0; pos=sum(r['sentiment']=='Positive' for r in cur); neg=sum(r['sentiment']=='Negative' for r in cur)
    concerns=sorted([x for x in category_stats if x['mentions']],key=lambda x:(x['negative'],x['negative_rate']),reverse=True)[:3]
    strengths=sorted([x for x in category_stats if x['mentions']],key=lambda x:(x['positive'],x['positive_rate']),reverse=True)[:3]
    action_map={'Wait Time':'Review staffing and kitchen throughput during the busiest service periods.','Service':'Review service standards and identify when customer attention breaks down.','Order Accuracy':'Audit order handoff/checking steps for dine-in and takeout orders.','Cleanliness':'Increase front-of-house and washroom cleanliness checks during peak periods.'}
    actions=[action_map.get(x['category'],f"Review the underlying {x['category'].lower()} complaints and identify a recurring operational cause.") for x in concerns if x['negative']>0][:3]
    drafts=[]
    for r in cur:
        if r['sentiment']!='Negative': continue
        primary=r['primary_category']
        drafts.append({'review_id':r['review_id'],'review_date':r['review_date'],'rating':r['rating'],'review':r['review'],'primary_category':primary,'review_reply_url':r.get('review_reply_url') or '','draft_response':f"Thank you for sharing your feedback. We're sorry your experience with {primary.lower()} did not meet expectations. We appreciate you bringing this to our attention and will review it with our team. We hope you'll give us another opportunity to provide a better experience."})
    brief={'headline':'Customer feedback needs attention' if alerts else 'Customer feedback is broadly stable','summary':f'{len(cur)} reviews were analyzed in the latest 30-day window with an average rating of {avg}.','top_concerns':[x['category'] for x in concerns],'top_strengths':[x['category'] for x in strengths],'recommended_actions':actions}
    out={'generated_at':datetime.now().isoformat(timespec='seconds'),'data_mode':data_mode,'source_file':source_file,'business':{'name':settings['business_name'],'location':settings['location_name']},'window':{'days':30,'start':cur_start.isoformat(),'end':latest.isoformat()},'metrics':{'reviews':len(cur),'average_rating':avg,'positive_pct':pct(pos,len(cur)),'negative_pct':pct(neg,len(cur)),'alerts':len(alerts)},'category_stats':category_stats,'menu_stats':menu,'monthly_trend':monthly,'alerts':alerts,'brief':brief,'response_drafts':drafts,'reviews':enriched}
    save_json(ROOT/'data.json',out); save_json(ROOT/'alerts.json',alerts); save_json(ROOT/'response_drafts.json',drafts)
    print(f"Analyzed {len(enriched)} reviews; current30={len(cur)}; alerts={len(alerts)}; mode={data_mode}")
if __name__=='__main__': run()
