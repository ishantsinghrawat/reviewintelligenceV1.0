from __future__ import annotations

from datetime import datetime
from pathlib import Path
import html

from common import ROOT, load_json


def esc(value):
    return html.escape(str(value if value is not None else ""))


def write_markdown(data):
    """Keep a markdown copy for GitHub/history, but the website uses HTML."""
    b = data.get("brief", {})
    m = data.get("metrics", {})
    business = data.get("business", {})
    window = data.get("window", {})

    lines = [
        "# Weekly Restaurant Customer Intelligence",
        "",
        f"**{business.get('name','Restaurant')} – {business.get('location','')}**",
        f"Window: {window.get('start','')} to {window.get('end','')}",
        "",
        f"- Reviews: **{m.get('reviews',0)}**",
        f"- Average rating: **{m.get('average_rating',0)} / 5**",
        f"- Positive: **{m.get('positive_pct',0)}%**",
        f"- Negative: **{m.get('negative_pct',0)}%**",
        f"- Active alerts: **{m.get('alerts',0)}**",
        "",
        f"## {b.get('headline','Customer feedback summary')}",
        b.get("summary",""),
        "",
        "## Top concerns",
    ]
    lines += [f"- {x}" for x in b.get("top_concerns", [])] or ["- None"]
    lines += ["", "## Top strengths"]
    lines += [f"- {x}" for x in b.get("top_strengths", [])] or ["- None"]
    lines += ["", "## Recommended actions"]
    lines += [f"- {x}" for x in b.get("recommended_actions", [])] or ["- No action required"]
    lines.append("")

    (ROOT / "weekly_report.md").write_text("\n".join(lines), encoding="utf-8")


def metric_card(label, value, note=""):
    return f"""
      <div class="card metric">
        <div class="k">{esc(label)}</div>
        <div class="v">{esc(value)}</div>
        <div class="metric-note">{esc(note)}</div>
      </div>
    """


def build_html(data):
    b = data.get("brief", {})
    m = data.get("metrics", {})
    business = data.get("business", {})
    window = data.get("window", {})
    alerts = data.get("alerts", [])
    categories = [x for x in data.get("category_stats", []) if x.get("mentions", 0)]
    categories.sort(key=lambda x: (x.get("negative", 0), x.get("negative_rate", 0)), reverse=True)
    menu = data.get("menu_stats", [])[:8]

    concerns = "".join(f"<span>{esc(x)}</span>" for x in b.get("top_concerns", [])) or "<span>None</span>"
    strengths = "".join(f"<span>{esc(x)}</span>" for x in b.get("top_strengths", [])) or "<span>None</span>"
    actions = "".join(f"<li>{esc(x)}</li>" for x in b.get("recommended_actions", [])) or "<li>No action required.</li>"

    alert_html = ""
    if alerts:
        for a in alerts:
            alert_html += f"""
              <div class="alert-box">
                <div class="alert-top">
                  <strong>{esc(a.get('category'))}</strong>
                  <span>{esc(a.get('severity',''))}</span>
                </div>
                <p>{esc(a.get('current_negative',0))} negative mentions in the latest 7 days vs
                   {esc(a.get('previous_negative',0))} in the prior 7 days.</p>
              </div>
            """
    else:
        alert_html = "<p class='sub'>No issue crossed the alert threshold this week.</p>"

    category_rows = "".join(
        f"""
          <tr>
            <td>{esc(x.get('category'))}</td>
            <td>{esc(x.get('mentions',0))}</td>
            <td>{esc(x.get('negative',0))}</td>
            <td>{round(float(x.get('negative_rate',0))*100)}%</td>
          </tr>
        """
        for x in categories[:8]
    )

    menu_rows = "".join(
        f"""
          <tr>
            <td>{esc(x.get('item'))}</td>
            <td>{esc(x.get('mentions',0))}</td>
            <td>{esc(x.get('positive_pct',0))}%</td>
            <td>{esc(x.get('negative_pct',0))}%</td>
            <td>{esc(x.get('avg_rating',0))}</td>
          </tr>
        """
        for x in menu
    )

    generated = data.get("generated_at", datetime.now().isoformat(timespec="seconds"))
    mode = "LIVE CUSTOMER DATA" if data.get("data_mode") == "real" else "DEMO DATA"
    mode_class = "live" if data.get("data_mode") == "real" else "demo"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Weekly Report · Restaurant Review Intelligence</title>
  <link rel="stylesheet" href="assets/css/app.css?v=1.6">
</head>
<body>
<header>
  <div>
    <h1>Restaurant Review Intelligence</h1>
    <div class="header-sub">Customer feedback → operational action</div>
  </div>
  <nav>
    <a href="index.html">Overview</a>
    <a href="reviews.html">Review Explorer</a>
    <a href="responses.html">Response Assistant</a>
    <a class="active" href="weekly_report.html">Weekly Report</a>
  </nav>
</header>

<main>
  <div class="hero">
    <div>
      <div class="eyebrow">Weekly intelligence report</div>
      <h1>{esc(business.get('name','Restaurant'))}</h1>
      <div class="sub">{esc(business.get('location',''))} · {esc(window.get('start',''))} to {esc(window.get('end',''))}</div>
    </div>
    <div class="mode-badge {mode_class}">{mode}</div>
  </div>

  <div class="grid section">
    {metric_card("Reviews", m.get("reviews",0), "latest 30 days")}
    {metric_card("Avg rating", f"⭐ {m.get('average_rating',0)}", "out of 5")}
    {metric_card("Positive", f"{m.get('positive_pct',0)}%", "4–5 star reviews")}
    {metric_card("Negative", f"{m.get('negative_pct',0)}%", "1–2 star reviews")}
    {metric_card("Alerts", m.get("alerts",0), "latest 7-day checks")}
  </div>

  <div class="two section">
    <section class="card">
      <div class="eyebrow">Executive summary</div>
      <h2>{esc(b.get("headline","Customer feedback summary"))}</h2>
      <p>{esc(b.get("summary",""))}</p>

      <div class="brief-label">Top concerns</div>
      <div class="chip-row">{concerns}</div>

      <div class="brief-label">Top strengths</div>
      <div class="chip-row">{strengths}</div>

      <div class="brief-label">Recommended actions</div>
      <ol>{actions}</ol>
    </section>

    <section class="card">
      <h2>Active alerts</h2>
      {alert_html}
    </section>
  </div>

  <section class="card section">
    <h2>Highest-impact issues</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>Issue</th><th>Mentions</th><th>Negative</th><th>Negative rate</th></tr>
        </thead>
        <tbody>{category_rows}</tbody>
      </table>
    </div>
  </section>

  <section class="card section">
    <h2>Menu intelligence</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>Dish</th><th>Mentions</th><th>Positive</th><th>Negative</th><th>Avg rating</th></tr>
        </thead>
        <tbody>{menu_rows or '<tr><td colspan="5">No menu-item data for this period.</td></tr>'}</tbody>
      </table>
    </div>
  </section>

  <div class="report-footer">
    Generated {esc(generated)} · This report summarizes review evidence and does not post or modify customer reviews.
  </div>
</main>
</body>
</html>
"""


def run():
    data = load_json(ROOT / "data.json")
    write_markdown(data)

    html_report = build_html(data)
    (ROOT / "weekly_report.html").write_text(html_report, encoding="utf-8")

    reports_dir = ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    stamp = data.get("window", {}).get("end") or datetime.now().date().isoformat()
    (reports_dir / f"{stamp}.html").write_text(html_report, encoding="utf-8")

    print("Generated weekly_report.html and weekly_report.md")


if __name__ == "__main__":
    run()
