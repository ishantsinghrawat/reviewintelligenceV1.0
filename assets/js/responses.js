let DATA = [];

const esc = s =>
  String(s ?? "").replace(/[&<>"]/g, c => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;"
  }[c]));

fetch("data.json?v=1.5-review-link")
  .then(r => r.json())
  .then(d => {
    DATA = d.response_drafts || [];

    const categories = [...new Set(
      DATA.map(x => x.primary_category)
    )].sort();

    const sel = document.getElementById("category");

    categories.forEach(c => {
      const o = document.createElement("option");
      o.value = c;
      o.textContent = c;
      sel.appendChild(o);
    });

    render();
  });

function filtered() {
  const category = document.getElementById("category").value;
  const rating = document.getElementById("rating").value;
  const q = document.getElementById("q").value.toLowerCase().trim();

  return DATA.filter(x =>
    (!category || x.primary_category === category) &&
    (!rating || String(x.rating) === rating) &&
    (!q || String(x.review || "").toLowerCase().includes(q))
  );
}

function render() {
  const rows = filtered();

  document.getElementById("count").innerHTML =
    `<strong>${rows.length}</strong> draft responses`;

  document.getElementById("responses").innerHTML =
    rows.map((x, i) => {
      const link = String(x.review_reply_url || "").trim();

      const reviewLink = link
        ? `
          <a
            class="review-link-btn"
            href="${esc(link)}"
            target="_blank"
            rel="noopener noreferrer"
          >
            Open review on Google ↗
          </a>
        `
        : `
          <span class="no-review-link">
            No Google link available
          </span>
        `;

      return `
        <div class="response-card">

          <div class="meta">
            ${esc(x.review_date)}
            · ⭐ ${x.rating}
            · ${esc(x.primary_category)}
          </div>

          <div class="review-quote">
            ${esc(x.review)}
          </div>

          <label for="draft-${i}">Suggested response</label>

          <textarea id="draft-${i}">${esc(x.draft_response)}</textarea>

          <div class="response-actions">

            <button type="button" onclick="copyDraft(${i}, this)">
              Copy response
            </button>

            ${reviewLink}

          </div>

        </div>
      `;
    }).join("");
}

async function copyDraft(i, button) {
  const el = document.getElementById(`draft-${i}`);

  try {
    await navigator.clipboard.writeText(el.value);

    const oldText = button.textContent;
    button.textContent = "Copied";

    setTimeout(() => {
      button.textContent = oldText;
    }, 1200);

  } catch (err) {
    el.select();
    document.execCommand("copy");
  }
}

["category", "rating", "q"].forEach(id => {
  document
    .getElementById(id)
    .addEventListener(
      id === "q" ? "input" : "change",
      render
    );
});
