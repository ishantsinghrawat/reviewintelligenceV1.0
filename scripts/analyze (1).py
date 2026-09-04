from __future__ import annotations
import csv, re, hashlib
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from common import ROOT, load_json, save_json, review_id, sentiment_from_rating

POSITIVE={"amazing","awesome","best","delicious","excellent","fantastic","fresh","friendly","good","great","helpful","love","loved","nice","perfect","quick","tasty","wonderful","warm","hot","attentive","polite","clean","generous","reasonable","fast","prompt","beautiful","cozy","recommend"}
NEGATIVE={"awful","bad","bland","cold","dirty","disappointing","expensive","late","missing","overpriced","poor","rude","slow","stale","terrible","unacceptable","wrong","worst","tiny","small","long","ignored","dry","burnt","undercooked","overcooked","soggy","noisy","loud","messy","greasy"}
NEGATORS={"not","never","no","hardly","wasnt","wasn't","isnt","isn't","didnt","didn't","dont","don't"}
INTENSIFIERS={"very","really","extremely","super","so","absolutely","incredibly","ridiculously"}

CATEGORY_PHRASES={
"Food Quality":[r"cold food",r"food was cold",r"not fresh",r"stale",r"undercooked",r"overcooked",r"burnt",r"soggy",r"dry food",r"food quality"],
"Taste":[r"delicious",r"tasty",r"bland",r"too salty",r"too spicy",r"flavou?r",r"tasted",r"taste"],
"Portion Size":[r"portion",r"serving size",r"too small",r"tiny portion",r"quantity",r"not enough food"],
"Price / Value":[r"overpriced",r"too expensive",r"not worth",r"worth the price",r"good value",r"price",r"value for money"],
"Service":[r"service",r"our server",r"waiter",r"waitress",r"being served",r"get.*attention",r"ignored us"],
"Staff Behaviour":[r"rude staff",r"friendly staff",r"helpful staff",r"staff.*attitude",r"manager",r"polite",r"unprofessional"],
"Wait Time":[r"waited?\s+\d+",r"\d+\s*(minutes?|mins?|hours?)",r"long wait",r"waited forever",r"took forever",r"took too long",r"slow service",r"quick service",r"no wait"],
"Order Accuracy":[r"wrong order",r"missing item",r"forgot.*order",r"incorrect order",r"order.*wrong",r"missing.*food"],
"Cleanliness":[r"dirty",r"not clean",r"clean table",r"clean restaurant",r"washroom",r"hygiene",r"messy table"],
"Ambience":[r"ambience",r"atmosphere",r"vibe",r"decor",r"too loud",r"noisy",r"music"],
"Delivery / Takeout":[r"delivery",r"takeout",r"take out",r"pickup",r"uber eats",r"doordash",r"packaging"],
"Parking / Accessibility":[r"parking",r"wheelchair",r"accessib",r"entrance"],
"Menu Availability":[r"sold out",r"not available",r"unavailable",r"out of stock",r"were out of",r"menu item.*available"]}

ACTION_MAP={
"Food Quality":"Audit preparation consistency and holding times for the dishes appearing in recent complaints.",
"Taste":"Review the dishes repeatedly associated with taste complaints and check recipe/seasoning consistency.",
"Portion Size":"Check portion consistency and whether serving size matches the price customers are paying.",
"Price / Value":"Review value perception by comparing price complaints with portion-size and food-quality feedback.",
"Service":"Review service handoffs and identify where guests stop receiving timely attention.",
"Staff Behaviour":"Review recent staff-interaction complaints with the front-of-house team and reinforce service standards.",
"Wait Time":"Review staffing, seating flow and kitchen throughput during the service periods connected to long waits.",
"Order Accuracy":"Add or reinforce a final order check before dine-in, pickup and delivery handoff.",
"Cleanliness":"Increase dining-room and washroom checks during busy periods and assign clear ownership.",
"Ambience":"Review recurring ambience complaints such as noise, seating comfort or music volume.",
"Delivery / Takeout":"Audit packaging, pickup handoff and delivery preparation for the complaints appearing most often.",
"Parking / Accessibility":"Make parking/access information clearer and address recurring accessibility barriers where possible.",
"Menu Availability":"Track frequently unavailable items and align prep/inventory levels with demand."}

def norm(s): return re.sub(r"\s+"," ",(s or "").lower().strip())
def split_sentences(text): return [p.strip() for p in re.split(r"(?<=[.!?])\s+|[;\n]+|\s+but\s+|\s+however\s+",text or "",flags=re.I) if p.strip()]
def words(text): return re.findall(r"[a-zA-Z']+",norm(text))

def local_sentiment(text,rating=3):
    toks=words(text); score=0.0
    for i,t in enumerate(toks):
        val=1 if t in POSITIVE else (-1 if t in NEGATIVE else 0)
        if not val: continue
        prev=toks[max(0,i-3):i]
        if any(x in NEGATORS for x in prev): val*=-1
        if any(x in INTENSIFIERS for x in prev): val*=1.4
        score+=val
    low=norm(text)
    if re.search(r"worth (the )?wait|no wait|didn['’]?t (have to )?wait",low): score+=1.5
    if re.search(r"not (bad|terrible|awful)",low): score+=1.0
    if re.search(r"not (good|great|fresh|clean|worth)",low): score-=1.2
    if score>=.75: return "Positive",min(.97,.62+min(4,abs(score))*.07)
    if score<=-.75: return "Negative",min(.97,.62+min(4,abs(score))*.07)
    return sentiment_from_rating(rating),.48

def _keyword_hit(sentence,kw):
    kw=norm(kw); s=norm(sentence)
    if " " in kw: return kw in s
    return re.search(r"(?<![a-z])"+re.escape(kw)+r"(?![a-z])",s) is not None

def classify_aspects(text,taxonomy,rating):
    """
    Classify a review into one or more restaurant aspects.

    Supports both:
    - V2 taxonomy: {"categories": [...], "keywords": {...}}
    - V1.5/test taxonomy: {"keywords": {...}}
    """
    sentences=split_sentences(text); out={}

    configured_categories=taxonomy.get("categories")
    legacy_taxonomy=not bool(configured_categories)
    categories=configured_categories or list(taxonomy.get("keywords",{}).keys())

    for cat in categories:
        kws=taxonomy.get("keywords",{}).get(cat,[]); evidence=[]; hits=[]
        for sentence in sentences:
            phrase_hits=[p for p in CATEGORY_PHRASES.get(cat,[]) if re.search(p,norm(sentence))]
            keyword_hits=[kw for kw in kws if _keyword_hit(sentence,kw)]
            if phrase_hits or keyword_hits:
                evidence.append(sentence); hits.extend(keyword_hits); hits.extend(phrase_hits)

        if not evidence:
            continue

        evidence=list(dict.fromkeys(evidence))
        sent,conf=local_sentiment(" ".join(evidence),rating)

        if cat=="Wait Time" and not legacy_taxonomy:
            strong=any(re.search(p,norm(text)) for p in CATEGORY_PHRASES["Wait Time"])
            if not strong and set(norm(x) for x in hits)<={"wait","waiting","slow","late","quick","minutes"}:
                continue

        score=min(.98,.62+.06*min(5,len(set(hits)))+.03*min(3,len(evidence)))
        out[cat]={
            "category":cat,
            "score":round(score,3),
            "sentiment":sent,
            "sentiment_confidence":round(conf,3),
            "hits":sorted(set(hits))[:8],
            "evidence":evidence[:3]
        }

    if not out:
        out["Food Quality"]={
            "category":"Food Quality",
            "score":.35,
            "sentiment":sentiment_from_rating(rating),
            "sentiment_confidence":.35,
            "hits":[],
            "evidence":[text] if text else []
        }

    return sorted(
        out.values(),
        key=lambda x:(x["score"],x["sentiment"]=="Negative"),
        reverse=True
    )

def find_menu(text,items):
    t=norm(text); return [x for x in items if norm(x) in t]

def load_reviews():
    real=ROOT/"data/reviews.csv"; sample=ROOT/"data/sample_reviews.csv"; p=real if real.exists() else sample
    with open(p,encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    return rows,p.name,("real" if real.exists() else "demo")

def pct(n,d): return round(100*n/d,1) if d else 0
def safe_date(v):
    try: return datetime.fromisoformat(str(v)[:10]).date()
    except Exception: return None

def rollup(items,categories):
    s={c:{"mentions":0,"positive":0,"neutral":0,"negative":0} for c in categories}
    for r in items:
        for a in r["aspects"]:
            x=s[a["category"]]; x["mentions"]+=1; x[a["sentiment"].lower()]+=1
    return s

def severity_weight(rating): return {1:1.0,2:.8,3:.45,4:.15,5:.05}.get(int(rating),.45)

def priority_score(cat,current_reviews,current_roll,prior_roll):
    row=current_roll[cat]; prior=prior_roll[cat]; neg=row["negative"]
    if not row["mentions"] or not neg: return 0
    affected=[r for r in current_reviews if any(a["category"]==cat and a["sentiment"]=="Negative" for a in r["aspects"])]
    severity=sum(severity_weight(r["rating"]) for r in affected)/len(affected) if affected else 0
    total_negative=max(1,sum(1 for r in current_reviews if r["sentiment"]=="Negative")); share=neg/total_negative
    growth=(neg+1)/(prior["negative"]+1); frequency=min(1.0,neg/max(3,len(current_reviews)*.20))
    score=100*(.35*frequency+.30*severity+.20*min(1,share*2)+.15*min(1,min(2,growth)/2))
    return round(min(100,score),1)

def pair_patterns(items):
    counts=Counter(); ratings=defaultdict(list); ids=defaultdict(list)
    for r in items:
        cats=sorted({a["category"] for a in r["aspects"]})
        for i in range(len(cats)):
            for j in range(i+1,len(cats)):
                p=(cats[i],cats[j]); counts[p]+=1; ratings[p].append(r["rating"]); ids[p].append(r["review_id"])
    out=[]
    for pair,n in counts.most_common():
        if n<2: continue
        out.append({"categories":list(pair),"reviews":n,"average_rating":round(sum(ratings[pair])/len(ratings[pair]),2),"review_ids":ids[pair][:8]})
    return out[:8]

def representative_evidence(cat,items,limit=2):
    rows=[]
    for r in items:
        for a in r["aspects"]:
            if a["category"]==cat and a["sentiment"]=="Negative":
                rows.append({"review_id":r["review_id"],"rating":r["rating"],"text":r["review"],"evidence":a.get("evidence",[])[:1]}); break
    return sorted(rows,key=lambda x:x["rating"])[:limit]

def response_draft(r):
    neg=[a["category"] for a in r["aspects"] if a["sentiment"]=="Negative"]
    pos=[a["category"] for a in r["aspects"] if a["sentiment"]=="Positive"]
    menu=r.get("menu_items",[]); seed=int(hashlib.sha1(r["review_id"].encode()).hexdigest()[:6],16)
    parts=[["Thank you for taking the time to share this feedback.","Thanks for letting us know about your experience.","We appreciate you taking the time to leave this review."][seed%3]]
    if pos:
        if menu and any(x in pos for x in ("Taste","Food Quality")): parts.append(f"We're glad you enjoyed the {menu[0]}.")
        elif "Taste" in pos or "Food Quality" in pos: parts.append("We're glad you enjoyed the food.")
        elif "Service" in pos or "Staff Behaviour" in pos: parts.append("We're pleased that part of your service experience was positive.")
    if neg:
        labels=neg[:2]; issue=labels[0].lower() if len(labels)==1 else f"{labels[0].lower()} and {labels[1].lower()}"
        parts.append(f"We're sorry that the {issue} fell short of what you expected.")
        parts.append("We'll use your feedback with our team as we work to improve the guest experience.")
    else: parts.append("We're happy to hear you had a positive experience and appreciate your support.")
    parts.append("We hope we have the opportunity to provide a better experience next time." if r["rating"]<=2 and neg else "We hope to welcome you again soon.")
    return " ".join(parts)

def run():
    tax=load_json(ROOT/"config/taxonomy.json"); settings=load_json(ROOT/"config/settings.json"); raw,source_file,data_mode=load_reviews(); enriched=[]
    for r in raw:
        try: rating=max(1,min(5,int(float(r.get("rating") or 3))))
        except Exception: rating=3
        text=r.get("review","") or ""; aspects=classify_aspects(text,tax,rating); rid=(r.get("review_id") or "").strip() or review_id(r)
        enriched.append({**r,"review_id":rid,"rating":rating,"sentiment":sentiment_from_rating(rating),"primary_category":aspects[0]["category"],"aspects":aspects,"menu_items":find_menu(text,tax["menu_items"]),"review_reply_url":(r.get("review_reply_url") or r.get("review_url") or "").strip()})
    enriched=[r for r in enriched if safe_date(r.get("review_date"))]; enriched.sort(key=lambda x:x.get("review_date",""),reverse=True)
    if not enriched: raise SystemExit("No valid dated reviews found.")
    latest=max(safe_date(r["review_date"]) for r in enriched); cur_start=latest-timedelta(days=29); prev_start=latest-timedelta(days=59)
    cur=[r for r in enriched if safe_date(r["review_date"])>=cur_start]; prev=[r for r in enriched if prev_start<=safe_date(r["review_date"])<cur_start]
    cr,pr=rollup(cur,tax["categories"]),rollup(prev,tax["categories"]); category_stats=[]
    for c in tax["categories"]:
        a,b=cr[c],pr[c]; affected=[r for r in cur if any(x["category"]==c for x in r["aspects"])]; avg_rating=round(sum(r["rating"] for r in affected)/len(affected),2) if affected else 0
        category_stats.append({"category":c,**a,"negative_rate":round(a["negative"]/a["mentions"],3) if a["mentions"] else 0,"positive_rate":round(a["positive"]/a["mentions"],3) if a["mentions"] else 0,"prior_mentions":b["mentions"],"prior_negative":b["negative"],"negative_change":a["negative"]-b["negative"],"average_rating":avg_rating,"priority_score":priority_score(c,cur,cr,pr)})
    l7s=latest-timedelta(days=6); p7s=latest-timedelta(days=13); l7=[r for r in enriched if safe_date(r["review_date"])>=l7s]; p7=[r for r in enriched if p7s<=safe_date(r["review_date"])<l7s]
    lr,pr7=rollup(l7,tax["categories"]),rollup(p7,tax["categories"]); alerts=[]; min_m=settings.get("alert",{}).get("min_mentions",4); ratio_min=settings.get("alert",{}).get("increase_ratio",1.5)
    for c in tax["categories"]:
        now,before=lr[c]["negative"],pr7[c]["negative"]; ratio=(now/before) if before else (999 if now else 0)
        if now>=min_m and ratio>=ratio_min: alerts.append({"category":c,"current_negative":now,"previous_negative":before,"increase_ratio":None if ratio==999 else round(ratio,2),"severity":"High" if now>=8 or ratio>=2 else "Medium","window":"latest 7 days vs prior 7 days"})
    trend=defaultdict(lambda:{"reviews":0,"rating_total":0,"positive":0,"negative":0})
    for r in enriched:
        m=r["review_date"][:7]; t=trend[m]; t["reviews"]+=1; t["rating_total"]+=r["rating"]; t["positive"]+=r["sentiment"]=="Positive"; t["negative"]+=r["sentiment"]=="Negative"
    monthly=[{"month":m,"reviews":t["reviews"],"average_rating":round(t["rating_total"]/t["reviews"],2),"positive_pct":pct(t["positive"],t["reviews"]),"negative_pct":pct(t["negative"],t["reviews"])} for m,t in sorted(trend.items())]
    menu=[]
    for item in tax["menu_items"]:
        rr=[r for r in cur if item in r["menu_items"]]
        if not rr: continue
        pos=neg=neu=0
        for r in rr:
            relevant=" ".join(s for s in split_sentences(r["review"]) if norm(item) in norm(s)); sent,_=local_sentiment(relevant or r["review"],r["rating"]); pos+=sent=="Positive"; neg+=sent=="Negative"; neu+=sent=="Neutral"
        menu.append({"item":item,"mentions":len(rr),"positive":pos,"negative":neg,"neutral":neu,"positive_pct":pct(pos,len(rr)),"negative_pct":pct(neg,len(rr)),"avg_rating":round(sum(r["rating"] for r in rr)/len(rr),2)})
    menu.sort(key=lambda x:(x["mentions"],x["positive_pct"]),reverse=True)
    ratings=[r["rating"] for r in cur]; avg=round(sum(ratings)/len(ratings),2) if ratings else 0; pos=sum(r["sentiment"]=="Positive" for r in cur); neg=sum(r["sentiment"]=="Negative" for r in cur)
    ranked=sorted([x for x in category_stats if x["mentions"] and x["negative"]],key=lambda x:(x["priority_score"],x["negative"]),reverse=True); priorities=[]
    for x in ranked[:3]:
        change=x["negative_change"]; direction="increased" if change>0 else ("decreased" if change<0 else "was unchanged")
        priorities.append({"rank":len(priorities)+1,"category":x["category"],"priority_score":x["priority_score"],"severity":"High" if x["priority_score"]>=65 else ("Medium" if x["priority_score"]>=40 else "Low"),"negative_mentions":x["negative"],"mentions":x["mentions"],"negative_rate":round(x["negative_rate"]*100,1),"average_rating":x["average_rating"],"negative_change":change,"summary":f'{x["category"]} has {x["negative"]} negative mentions across {x["mentions"]} mentions; negative volume {direction} by {abs(change)} vs the prior 30-day window.',"recommended_action":ACTION_MAP.get(x["category"],f'Review recurring {x["category"].lower()} complaints and identify the operational cause.'),"evidence":representative_evidence(x["category"],cur)})
    patterns=[]
    for p in pair_patterns(cur)[:4]:
        a,b=p["categories"]; patterns.append({"title":f"{a} + {b}","summary":f'{p["reviews"]} recent reviews mention both {a.lower()} and {b.lower()}; those reviews average {p["average_rating"]} stars.',"reviews":p["reviews"],"average_rating":p["average_rating"],"review_ids":p["review_ids"]})
    strengths=sorted([x for x in category_stats if x["mentions"]],key=lambda x:(x["positive"],x["positive_rate"]),reverse=True)[:3]; drafts=[]
    for r in cur:
        if r["sentiment"]!="Negative": continue
        drafts.append({"review_id":r["review_id"],"review_date":r["review_date"],"rating":r["rating"],"review":r["review"],"primary_category":r["primary_category"],"negative_aspects":[a["category"] for a in r["aspects"] if a["sentiment"]=="Negative"],"positive_aspects":[a["category"] for a in r["aspects"] if a["sentiment"]=="Positive"],"menu_items":r["menu_items"],"review_reply_url":r.get("review_reply_url",""),"draft_response":response_draft(r),"response_mode":"V2 contextual template"})
    if priorities:
        lead=priorities[0]; headline=f'Top priority: {lead["category"]}'; summary=f'{len(cur)} reviews were analyzed in the latest 30 days. Average rating is {avg}. {lead["category"]} has the highest operational priority score ({lead["priority_score"]}/100).'
    else: headline="No major negative issue dominates the current window"; summary=f"{len(cur)} reviews were analyzed in the latest 30 days with an average rating of {avg}."
    brief={"headline":headline,"summary":summary,"top_concerns":[x["category"] for x in ranked[:3]],"top_strengths":[x["category"] for x in strengths],"recommended_actions":[x["recommended_action"] for x in priorities],"priority_issues":priorities,"patterns":patterns}
    out={"analysis_version":"2.0","generated_at":datetime.now().isoformat(timespec="seconds"),"data_mode":data_mode,"source_file":source_file,"business":{"name":settings["business_name"],"location":settings["location_name"]},"window":{"days":30,"start":cur_start.isoformat(),"end":latest.isoformat()},"metrics":{"reviews":len(cur),"average_rating":avg,"positive_pct":pct(pos,len(cur)),"negative_pct":pct(neg,len(cur)),"alerts":len(alerts)},"category_stats":category_stats,"priority_issues":priorities,"patterns":patterns,"menu_stats":menu,"monthly_trend":monthly,"alerts":alerts,"brief":brief,"response_drafts":drafts,"reviews":enriched}
    save_json(ROOT/"data.json",out); save_json(ROOT/"alerts.json",alerts); save_json(ROOT/"response_drafts.json",drafts)
    print(f"V2 analyzed {len(enriched)} reviews; current30={len(cur)}; priorities={len(priorities)}; alerts={len(alerts)}; mode={data_mode}")
if __name__=="__main__": run()
