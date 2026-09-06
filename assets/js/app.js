const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const sign=n=>n>0?`+${n}`:String(n);
function confidence(c){return `<span class="confidence ${String(c).toLowerCase().replace(' ','-')}">${esc(c)}</span>`}
function bar(value,max,label){const width=max?Math.max(4,Math.round((value/max)*100)):0;return `<div class="mini-bar-row"><span>${esc(label)}</span><div class="mini-bar"><div style="width:${width}%"></div></div><strong>${value}</strong></div>`}

fetch('data.json?v=2.1').then(r=>{if(!r.ok)throw new Error(`data.json ${r.status}`);return r.json()}).then(d=>{
 const oi=d.operational_intelligence||{};
 document.getElementById('biz').textContent=`${d.business.name} — ${d.business.location}`;
 document.getElementById('window').textContent=`V${d.analysis_version||'2.1'} · ${d.window.start} to ${d.window.end} · ${oi.sample_confidence||''} confidence`;
 const mode=document.getElementById('modeBadge');mode.textContent=d.data_mode==='real'?'LIVE CUSTOMER DATA':'DEMO DATA';mode.className=`mode-badge ${d.data_mode==='real'?'live':'demo'}`;

 const m=d.metrics;
 const cards=[
   ['Restaurant health',`${oi.health_score??'—'}/100`,'review-derived operating signal'],
   ['Reviews',m.reviews,'latest 30 days'],
   ['Avg rating','⭐ '+m.average_rating,'out of 5'],
   ['Negative',m.negative_pct+'%','1–2 star reviews'],
   ['Alerts',m.alerts,'7-day anomaly checks']
 ];
 document.getElementById('metrics').innerHTML=cards.map((x,i)=>`<div class="card metric ${i===0?'health-card':''}"><div class="k">${x[0]}</div><div class="v">${x[1]}</div><div class="metric-note">${x[2]}</div></div>`).join('');

 const ps=oi.priorities||[];
 document.getElementById('issues').innerHTML=ps.length?`
   <div class="v21-stack">${ps.slice(0,3).map((x,i)=>`
     <div class="priority-card">
       <div class="priority-top"><div><span class="rank">#${i+1}</span> <strong>${esc(x.category)}</strong></div><div><strong>${Math.round(x.score)}/100</strong> ${confidence(x.confidence)}</div></div>
       <div class="priority-evidence">${esc(x.why_it_matters)}</div>
       <div class="priority-stats"><span>${x.negative_mentions} negative</span><span>${x.negative_rate}% negative rate</span><span>${sign(x.negative_change)} vs prior period</span></div>
       <div class="action"><strong>Investigate:</strong> ${esc(x.action)}</div>
       <a href="reviews.html?category=${encodeURIComponent(x.category)}&sentiment=Negative">See supporting reviews →</a>
     </div>`).join('')}</div>`:'<p>No issue has enough negative evidence to prioritize yet.</p>';

 const roots=oi.root_cause_patterns||[], trade=oi.customer_tradeoffs||[];
 document.getElementById('brief').innerHTML=`
   <div class="brief-headline">${esc(d.brief?.headline||'Operational intelligence')}</div>
   <p>${esc(d.brief?.summary||'')}</p>
   ${roots.length?`<div class="brief-label">Likely root-cause relationships</div>${roots.slice(0,3).map(x=>`
     <div class="insight-box"><strong>${esc(x.title)}</strong> ${confidence(x.confidence)}
     <p>${esc(x.insight)}</p><div class="action"><strong>What to check:</strong> ${esc(x.action)}</div></div>`).join('')}:''}
   ${trade.length?`<div class="brief-label">Customer trade-offs</div>${trade.slice(0,2).map(x=>`
     <div class="insight-box"><strong>${esc(x.title)}</strong><p>${x.reviews} reviews · ${x.average_rating}★ average · ${esc(x.confidence)} confidence</p></div>`).join('')}:''}
   <p class="method-note">${esc(oi.method_note||'')}</p>`;

 if(!d.monthly_trend?.length) document.getElementById('trend').innerHTML='<p>No trend data yet.</p>';
 else {const mx=Math.max(...d.monthly_trend.map(x=>x.reviews));document.getElementById('trend').innerHTML=d.monthly_trend.slice(-6).map(x=>bar(x.reviews,mx,`${x.month} · ⭐ ${x.average_rating}`)).join('')}

 document.getElementById('alerts').innerHTML=d.alerts?.length?d.alerts.map(a=>`<div class="alert-box"><div class="alert-top"><strong>${esc(a.category)}</strong><span>${esc(a.severity)}</span></div><p>${a.current_negative} negative mentions in the latest 7 days vs ${a.previous_negative} in the prior 7 days.</p><a href="reviews.html?category=${encodeURIComponent(a.category)}&sentiment=Negative">View evidence →</a></div>`).join(''):'<p>No issue crossed the alert threshold this week.</p>';

 const menuLinks=oi.menu_issue_links||[];
 document.getElementById('menu').innerHTML=menuLinks.length?`<table><tr><th>Dish</th><th>Mentions</th><th>Avg rating</th><th>Operational signal</th></tr>${menuLinks.slice(0,12).map(x=>`<tr><td><strong>${esc(x.item)}</strong></td><td>${x.mentions}</td><td>${x.average_rating}★</td><td>${x.top_negative_issues?.length?x.top_negative_issues.map(i=>`${esc(i.category)} (${i.reviews})`).join(' · '):'No repeated negative issue'}<br><small>${esc(x.confidence)} confidence</small></td></tr>`).join('')}</table>`:'<p>No menu-item patterns detected yet.</p>';
}).catch(err=>{console.error(err);const el=document.getElementById('brief');if(el)el.innerHTML='<p>Dashboard data could not load. Open browser Console for details.</p>'});