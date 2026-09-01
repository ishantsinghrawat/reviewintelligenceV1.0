let DATA = [];
let CAT = "";

const esc = s => String(s ?? "").replace(/[&<>"]/g,c=>({
  "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"
}[c]));

function getQueryParams(){
  const p = new URLSearchParams(location.search);
  return {
    category: p.get("category") || "",
    sentiment: p.get("sentiment") || ""
  };
}

fetch("data.json?v=1.6")
  .then(r => r.json())
  .then(d => {
    DATA = d.reviews || [];
    const q = getQueryParams();
    CAT = q.category;

    if (q.sentiment) {
      document.getElementById("sent").value = q.sentiment;
    }

    buildCats(d.category_stats || []);
    render();
  });

function buildCats(stats){
  const el = document.getElementById("cats");
  el.innerHTML = "";

  const all = document.createElement("button");
  all.className = "cat" + (!CAT ? " active" : "");
  all.textContent = "All categories";
  all.onclick = () => setCat("", all);
  el.appendChild(all);

  stats
    .filter(x => x.mentions)
    .sort((a,b) => b.mentions-a.mentions)
    .forEach(x => {
      const b = document.createElement("button");
      b.className = "cat" + (CAT === x.category ? " active" : "");
      b.textContent = `${x.category} (${x.mentions})`;
      b.onclick = () => setCat(x.category,b);
      el.appendChild(b);
    });
}

function setCat(c,btn){
  CAT = c;
  document.querySelectorAll(".cat").forEach(x => x.classList.remove("active"));
  btn.classList.add("active");
  render();
}

function filtered(){
  const s = document.getElementById("sent").value;
  const r = document.getElementById("rating").value;
  const q = document.getElementById("q").value.toLowerCase().trim();

  return DATA.filter(x => {
    const matchingAspect = !CAT || (x.aspects || []).some(a =>
      a.category === CAT && (!s || a.sentiment === s)
    );

    const overallSentiment = !s || CAT || x.sentiment === s;
    const ratingMatch = !r || String(x.rating) === r;
    const textMatch = !q || (x.review || "").toLowerCase().includes(q);

    return matchingAspect && overallSentiment && ratingMatch && textMatch;
  });
}

function render(){
  const rows = filtered();
  const filterText = CAT ? `Showing ${CAT} reviews` : "Showing all reviews";

  document.getElementById("count").innerHTML = `
    <div><strong>${rows.length}</strong> reviews</div>
    <div class="review-count-sub">${esc(filterText)}</div>
  `;

  document.getElementById("reviews").innerHTML =
    rows.map(x => {
      const topicChips = (x.aspects || []).map(a =>
        `<span class="${String(a.sentiment || "").toLowerCase()}">${esc(a.category)}</span>`
      ).join("");

      const menuChips = (x.menu_items || []).map(m =>
        `<span class="menu-chip">${esc(m)}</span>`
      ).join("");

      return `
        <article class="review">
          <div class="meta">${esc(x.review_date)} · ⭐ ${x.rating} · ${esc(x.sentiment)} · ${esc(x.source)}</div>
          <p>${esc(x.review)}</p>
          <div class="chips">${topicChips}${menuChips}</div>
        </article>
      `;
    }).join("");
}

["sent","rating","q"].forEach(id =>
  document.getElementById(id).addEventListener(id==="q" ? "input" : "change", render)
);

document.getElementById("csv").onclick = () => {
  const rows = filtered();
  const cols = ["review_date","rating","sentiment","primary_category","review"];
  const out = [cols.join(",")];

  rows.forEach(x =>
    out.push(cols.map(c =>
      `"${String(x[c] ?? "").replaceAll('"','""')}"`
    ).join(","))
  );

  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([out.join("\n")], {type:"text/csv"}));
  a.download = "filtered_reviews.csv";
  a.click();
};
