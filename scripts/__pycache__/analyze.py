import csv
from collections import Counter
from datetime import datetime,timedelta
from common import ROOT,load_json,save_json,review_id,sentiment_from_rating

def classify(text,tax):
    t=(text or '').lower(); out=[]
    for cat,kws in tax['keywords'].items():
        hits=[k for k in kws if k in t]
        if hits: out.append({'category':cat,'score':min(.95,.55+.1*len(hits)),'hits':hits[:5]})
    return sorted(out,key=lambda x:x['score'],reverse=True) or [{'category':'Food Quality','score':.4,'hits':[]}]

def run():
    tax=load_json(ROOT/'config/taxonomy.json'); settings=load_json(ROOT/'config/settings.json')
    p=ROOT/'data/reviews.csv'
    if not p.exists(): p=ROOT/'data/sample_reviews.csv'
    with open(p,encoding='utf-8') as f: raw=list(csv.DictReader(f))
    reviews=[]
    for r in raw:
        aspects=classify(r.get('review',''),tax); rating=int(float(r.get('rating') or 3)); text=(r.get('review') or '').lower()
        reviews.append({**r,'review_id':review_id(r),'rating':rating,'sentiment':sentiment_from_rating(rating),'primary_category':aspects[0]['category'],'aspects':aspects,'menu_items':[m for m in tax['menu_items'] if m.lower() in text]})
    reviews.sort(key=lambda x:x['review_date'],reverse=True)
    end=max(datetime.fromisoformat(r['review_date']).date() for r in reviews); start=end-timedelta(days=29); prev_start=end-timedelta(days=59)
    cur=[r for r in reviews if datetime.fromisoformat(r['review_date']).date()>=start]
    prev=[r for r in reviews if prev_start<=datetime.fromisoformat(r['review_date']).date()<start]
    def counts(items):
        c,n,p=Counter(),Counter(),Counter()
        for r in items:
            for cat in {a['category'] for a in r['aspects']}:
                c[cat]+=1; n[cat]+=r['sentiment']=='Negative'; p[cat]+=r['sentiment']=='Positive'
        return c,n,p
    cc,cn,cp=counts(cur); pc,pn,pp=counts(prev); stats=[]; alerts=[]
    for cat in tax['categories']:
        mentions=cc[cat]; neg=cn[cat]; prior=pn[cat]; ratio=(neg/prior) if prior else (999 if neg else 0)
        stats.append({'category':cat,'mentions':mentions,'negative_mentions':neg,'positive_mentions':cp[cat],'negative_rate':round(neg/mentions,3) if mentions else 0,'prior_negative_mentions':prior,'change_ratio':None if ratio==999 else round(ratio,2)})
        if neg>=settings['alert']['min_mentions'] and ratio>=settings['alert']['increase_ratio']:
            alerts.append({'category':cat,'current_negative':neg,'previous_negative':prior,'increase_ratio':None if ratio==999 else round(ratio,2),'severity':'High' if neg>=8 or ratio>=2 else 'Medium'})
    menu=[]
    for item in tax['menu_items']:
        rr=[r for r in cur if item in r['menu_items']]
        if rr: menu.append({'item':item,'mentions':len(rr),'positive':sum(r['sentiment']=='Positive' for r in rr),'negative':sum(r['sentiment']=='Negative' for r in rr),'avg_rating':round(sum(r['rating'] for r in rr)/len(rr),2)})
    menu.sort(key=lambda x:x['mentions'],reverse=True)
    avg=round(sum(r['rating'] for r in cur)/len(cur),2) if cur else 0; pos=sum(r['sentiment']=='Positive' for r in cur); neg=sum(r['sentiment']=='Negative' for r in cur)
    topneg=sorted(stats,key=lambda x:x['negative_mentions'],reverse=True)[:3]; toppos=sorted(stats,key=lambda x:x['positive_mentions'],reverse=True)[:3]
    brief={'headline':'Customer feedback needs attention' if alerts else 'Customer feedback is broadly stable','summary':f'{len(cur)} reviews analyzed in the latest 30-day window with an average rating of {avg}.','top_concerns':[x['category'] for x in topneg if x['negative_mentions']],'top_strengths':[x['category'] for x in toppos if x['positive_mentions']],'recommended_actions':[f"Investigate {x['category'].lower()} complaints; {x['negative_mentions']} negative mentions were detected." for x in topneg if x['negative_mentions']]}
    out={'generated_at':datetime.now().isoformat(timespec='seconds'),'source_file':p.name,'business':{'name':settings['business_name'],'location':settings['location_name']},'window':{'days':30,'start':start.isoformat(),'end':end.isoformat()},'metrics':{'reviews':len(cur),'average_rating':avg,'positive_pct':round(100*pos/len(cur),1) if cur else 0,'negative_pct':round(100*neg/len(cur),1) if cur else 0,'alerts':len(alerts)},'category_stats':stats,'menu_stats':menu,'alerts':alerts,'brief':brief,'reviews':reviews}
    save_json(ROOT/'data.json',out); save_json(ROOT/'alerts.json',alerts); print(f'Analyzed {len(reviews)} reviews; current={len(cur)}; alerts={len(alerts)}')
if __name__=='__main__': run()
