const esc = s =>
  String(s ?? "").replace(/[&<>"]/g, c => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;"
  }[c]));

const sign = n => {
  const v = Number(n || 0);
  return v > 0 ? `+${v}` : String(v);
};

function confidence(label) {
  const text = String(label || "");
  const cls = text.toLowerCase().replace(/\s+/g, "-");

  return `
    <span class="confidence ${cls}">
      ${esc(text)}
    </span>
  `;
}

function bar(value, max, label) {
  const width = max
    ? Math.max(4, Math.round((value / max) * 100))
    : 0;

  return `
    <div class="mini-bar-row">
      <span>${esc(label)}</span>

      <div class="mini-bar">
        <div style="width:${width}%"></div>
      </div>

      <strong>${value}</strong>
    </div>
  `;
}

function renderPriority(x, index) {
  return `
    <div class="priority-card">

      <div class="priority-top">
        <div>
          <span class="rank">#${index + 1}</span>
          <strong>${esc(x.category)}</strong>
        </div>

        <div>
          <strong>
            ${Math.round(Number(x.score || 0))}/100
          </strong>

          ${confidence(x.confidence)}
        </div>
      </div>

      <div class="priority-evidence">
        ${esc(x.why_it_matters)}
      </div>

      <div class="priority-stats">

        <span>
          ${Number(x.negative_mentions || 0)} negative
        </span>

        <span>
          ${Number(x.negative_rate || 0)}% negative rate
        </span>

        <span>
          ${sign(x.negative_change)} vs prior period
        </span>

      </div>

      <div class="action">
        <strong>Investigate:</strong>
        ${esc(x.action)}
      </div>

      <a
        href="reviews.html?category=${encodeURIComponent(
          x.category || ""
        )}&sentiment=Negative"
      >
        See supporting reviews →
      </a>

    </div>
  `;
}

function renderRootCause(x) {
  return `
    <div class="insight-box">

      <strong>${esc(x.title)}</strong>

      ${confidence(x.confidence)}

      <p>
        ${esc(x.insight)}
      </p>

      <div class="action">
        <strong>What to check:</strong>
        ${esc(x.action)}
      </div>

    </div>
  `;
}

function renderTradeoff(x) {
  return `
    <div class="insight-box">

      <strong>
        ${esc(x.title)}
      </strong>

      <p>
        ${Number(x.reviews || 0)} reviews ·
        ${Number(x.average_rating || 0)}★ average ·
        ${esc(x.confidence)} confidence
      </p>

    </div>
  `;
}

function renderAlert(a) {
  return `
    <div class="alert-box">

      <div class="alert-top">

        <strong>
          ${esc(a.category)}
        </strong>

        <span>
          ${esc(a.severity)}
        </span>

      </div>

      <p>
        ${Number(a.current_negative || 0)}
        negative mentions in the latest 7 days
        vs
        ${Number(a.previous_negative || 0)}
        in the prior 7 days.
      </p>

      <a
        href="reviews.html?category=${encodeURIComponent(
          a.category || ""
        )}&sentiment=Negative"
      >
        View evidence →
      </a>

    </div>
  `;
}

function renderMenuRow(x) {

  const issues =
    Array.isArray(x.top_negative_issues) &&
    x.top_negative_issues.length

      ? x.top_negative_issues
          .map(
            i =>
              `${esc(i.category)} (${Number(
                i.reviews || 0
              )})`
          )
          .join(" · ")

      : "No repeated negative issue";

  return `
    <tr>

      <td>
        <strong>
          ${esc(x.item)}
        </strong>
      </td>

      <td>
        ${Number(x.mentions || 0)}
      </td>

      <td>
        ${Number(x.average_rating || 0)}★
      </td>

      <td>
        ${issues}

        <br>

        <small>
          ${esc(x.confidence)} confidence
        </small>
      </td>

    </tr>
  `;
}


/* =========================================
   LOAD DASHBOARD DATA
   ========================================= */

fetch("data.json?v=2.1.1")

  .then(r => {

    if (!r.ok) {
      throw new Error(
        `data.json ${r.status}`
      );
    }

    return r.json();

  })

  .then(d => {

    const oi =
      d.operational_intelligence || {};

    const business =
      d.business || {};

    const windowData =
      d.window || {};

    const metrics =
      d.metrics || {};


    /* =====================================
       RESTAURANT NAME
       ===================================== */

    const biz =
      document.getElementById("biz");

    if (biz) {

      const name =
        business.name || "Restaurant";

      const location =
        business.location || "";

      biz.textContent =
        location
          ? `${name} — ${location}`
          : name;
    }


    /* =====================================
       ANALYSIS WINDOW
       ===================================== */

    const windowEl =
      document.getElementById("window");

    if (windowEl) {

      const version =
        d.analysis_version || "2.1";

      const start =
        windowData.start || "";

      const end =
        windowData.end || "";

      const conf =
        oi.sample_confidence || "";

      windowEl.textContent =
        `V${version}` +

        (
          start && end
            ? ` · ${start} to ${end}`
            : ""
        ) +

        (
          conf
            ? ` · ${conf} confidence`
            : ""
        );
    }


    /* =====================================
       DATA MODE BADGE
       ===================================== */

    const mode =
      document.getElementById(
        "modeBadge"
      );

    if (mode) {

      const live =
        d.data_mode === "real";

      mode.textContent =
        live
          ? "LIVE CUSTOMER DATA"
          : "DEMO DATA";

      mode.className =
        `mode-badge ${
          live ? "live" : "demo"
        }`;
    }


    /* =====================================
       TOP METRICS
       ===================================== */

    const metricCards = [

      [
        "Restaurant health",
        `${oi.health_score ?? "—"}/100`,
        "review-derived operating signal"
      ],

      [
        "Reviews",
        metrics.reviews ?? 0,
        "latest 30 days"
      ],

      [
        "Avg rating",
        `⭐ ${
          metrics.average_rating ?? "—"
        }`,
        "out of 5"
      ],

      [
        "Negative",
        `${
          metrics.negative_pct ?? 0
        }%`,
        "1–2 star reviews"
      ],

      [
        "Alerts",
        metrics.alerts ?? 0,
        "7-day anomaly checks"
      ]

    ];

    const metricsEl =
      document.getElementById(
        "metrics"
      );

    if (metricsEl) {

      metricsEl.innerHTML =
        metricCards

          .map(
            (x, i) => `
              <div
                class="card metric ${
                  i === 0
                    ? "health-card"
                    : ""
                }"
              >

                <div class="k">
                  ${esc(x[0])}
                </div>

                <div class="v">
                  ${esc(x[1])}
                </div>

                <div class="metric-note">
                  ${esc(x[2])}
                </div>

              </div>
            `
          )

          .join("");
    }


    /* =====================================
       TOP OPERATIONAL PRIORITIES
       ===================================== */

    const priorities =
      Array.isArray(oi.priorities)
        ? oi.priorities
        : [];

    const issuesEl =
      document.getElementById(
        "issues"
      );

    if (issuesEl) {

      issuesEl.innerHTML =
        priorities.length

          ? `
            <div class="v21-stack">

              ${
                priorities
                  .slice(0, 3)
                  .map(renderPriority)
                  .join("")
              }

            </div>
          `

          : `
            <p>
              No issue has enough
              negative evidence to
              prioritize yet.
            </p>
          `;
    }


    /* =====================================
       OWNER BRIEF
       ===================================== */

    const roots =
      Array.isArray(
        oi.root_cause_patterns
      )
        ? oi.root_cause_patterns
        : [];

    const tradeoffs =
      Array.isArray(
        oi.customer_tradeoffs
      )
        ? oi.customer_tradeoffs
        : [];

    const briefParts = [];

    briefParts.push(`
      <div class="brief-headline">

        ${
          esc(
            d.brief?.headline ||
            "Operational intelligence"
          )
        }

      </div>
    `);

    if (d.brief?.summary) {

      briefParts.push(`
        <p>
          ${esc(d.brief.summary)}
        </p>
      `);
    }


    if (roots.length) {

      briefParts.push(`
        <div class="brief-label">
          Likely root-cause relationships
        </div>
      `);

      briefParts.push(
        roots
          .slice(0, 3)
          .map(renderRootCause)
          .join("")
      );
    }


    if (tradeoffs.length) {

      briefParts.push(`
        <div class="brief-label">
          Customer trade-offs
        </div>
      `);

      briefParts.push(
        tradeoffs
          .slice(0, 2)
          .map(renderTradeoff)
          .join("")
      );
    }


    if (oi.method_note) {

      briefParts.push(`
        <p class="method-note">
          ${esc(oi.method_note)}
        </p>
      `);
    }


    const briefEl =
      document.getElementById(
        "brief"
      );

    if (briefEl) {

      briefEl.innerHTML =
        briefParts.join("");
    }


    /* =====================================
       RATING TREND
       ===================================== */

    const trendEl =
      document.getElementById(
        "trend"
      );

    const trend =
      Array.isArray(d.monthly_trend)
        ? d.monthly_trend
        : [];


    if (trendEl) {

      if (!trend.length) {

        trendEl.innerHTML =
          "<p>No trend data yet.</p>";

      } else {

        const maxReviews =
          Math.max(
            ...trend.map(
              x =>
                Number(
                  x.reviews || 0
                )
            ),
            1
          );

        trendEl.innerHTML =
          trend

            .slice(-6)

            .map(
              x =>
                bar(
                  Number(
                    x.reviews || 0
                  ),

                  maxReviews,

                  `${
                    x.month || ""
                  } · ⭐ ${
                    x.average_rating ??
                    "—"
                  }`
                )
            )

            .join("");
      }
    }


    /* =====================================
       ACTIVE ALERTS
       ===================================== */

    const alertsEl =
      document.getElementById(
        "alerts"
      );

    const alerts =
      Array.isArray(d.alerts)
        ? d.alerts
        : [];


    if (alertsEl) {

      alertsEl.innerHTML =
        alerts.length

          ? alerts
              .map(renderAlert)
              .join("")

          : `
            <p>
              No issue crossed the
              alert threshold this week.
            </p>
          `;
    }


    /* =====================================
       MENU INTELLIGENCE
       ===================================== */

    const menuEl =
      document.getElementById(
        "menu"
      );

    const menuLinks =
      Array.isArray(
        oi.menu_issue_links
      )
        ? oi.menu_issue_links
        : [];


    if (menuEl) {

      menuEl.innerHTML =
        menuLinks.length

          ? `
            <table>

              <tr>
                <th>Dish</th>
                <th>Mentions</th>
                <th>Avg rating</th>
                <th>
                  Operational signal
                </th>
              </tr>

              ${
                menuLinks
                  .slice(0, 12)
                  .map(renderMenuRow)
                  .join("")
              }

            </table>
          `

          : `
            <p>
              No menu-item patterns
              detected yet.
            </p>
          `;
    }

  })


  /* =========================================
     ERROR HANDLING
     ========================================= */

  .catch(err => {

    console.error(
      "Restaurant Review Intelligence dashboard error:",
      err
    );

    const briefEl =
      document.getElementById(
        "brief"
      );

    if (briefEl) {

      briefEl.innerHTML = `
        <p>
          Dashboard data could not load.
          Check the browser Console for
          details.
        </p>
      `;
    }

  });
