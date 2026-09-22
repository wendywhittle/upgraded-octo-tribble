const app = document.getElementById("app");
const pipeline = document.getElementById("pipeline-list");
const detail = document.getElementById("detail");

async function api(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let message = "Request failed";
    try { message = (await response.json()).detail || message; } catch {}
    throw new Error(message);
  }
  return response;
}

async function loadDeals() {
  const response = await api("/api/deals");
  const deals = await response.json();
  pipeline.innerHTML = "";
  if (!deals.length) {
    pipeline.innerHTML = "<p>No deals submitted yet.</p>";
    return;
  }
  for (const deal of deals) {
    const record = document.createElement("article");
    record.className = "record";
    record.innerHTML = `<button class="record-button" type="button"><strong>${escapeHtml(deal.deal_id)}</strong><span>${escapeHtml(deal.original_inputs?.name || "")}</span><span>${escapeHtml(deal.status)}</span></button>`;
    record.querySelector("button").addEventListener("click", () => loadDeal(deal.deal_id));
    pipeline.appendChild(record);
  }
}

async function loadDeal(id) {
  const response = await api("/api/deals/" + encodeURIComponent(id));
  const deal = await response.json();
  const inputs = deal.original_inputs || {};
  const derived = deal.derived || {};
  const missing = deal.missing || [];

  detail.classList.remove("hidden");
  detail.innerHTML = `
    <div class="section-head">
      <p class="eyebrow">DEAL RECORD</p>
      <h2>${escapeHtml(deal.deal_id)}</h2>
      <p>${escapeHtml(inputs.name || "")}</p>
    </div>

    <div class="record">
      <h3>Original Inputs</h3>
      <p><strong>Asset:</strong> ${escapeHtml(inputs.asset_type || "Unavailable")}</p>
      <p><strong>Location:</strong> ${escapeHtml(inputs.location || "Unavailable")}</p>
      <p><strong>Purchase price:</strong> ${formatNumber(inputs.purchase_price)}</p>
      <p><strong>NOI:</strong> ${formatNumber(inputs.noi)}</p>
      <p><strong>EGI:</strong> ${formatNumber(inputs.egi)}</p>
      <p><strong>Operating expenses:</strong> ${formatNumber(inputs.operating_expenses)}</p>
      <p><strong>Occupancy:</strong> ${formatPercent(inputs.occupancy)}</p>
      <p><strong>LTV:</strong> ${formatPercent(inputs.ltv)}</p>
      <p><strong>Interest rate:</strong> ${formatPercent(inputs.interest_rate)}</p>
      <p><strong>Amortization:</strong> ${formatNumber(inputs.amortization_years)} years</p>
      <p><strong>Hold:</strong> ${formatNumber(inputs.hold_years)} years</p>
      <p><strong>Exit cap rate:</strong> ${formatPercent(inputs.exit_cap_rate)}</p>
      <p><strong>Closing costs:</strong> ${formatNumber(inputs.closing_costs)}</p>
    </div>

    <div class="record">
      <h3>Calculated Underwriting</h3>
      ${derivedRows(derived)}
    </div>

    <div class="record">
      <h3>Missing / Unavailable</h3>
      ${missing.length ? "<ul>" + missing.map(item => "<li>" + escapeHtml(item.replaceAll("_", " ")) + "</li>").join("") + "</ul>" : "<p>None identified.</p>"}
    </div>

    <div class="record">
      <p><strong>Status:</strong> ${escapeHtml(deal.status)}</p>
      <label>Pipeline status
        <select id="status-select">
          <option>NEW</option>
          <option>REVIEWING</option>
          <option>PURSUE</option>
          <option>HOLD</option>
          <option>PASS</option>
        </select>
      </label>
      <button id="save-status" class="primary" type="button">SAVE STATUS</button>
      <a class="nav-button" href="/api/deals/${encodeURIComponent(deal.deal_id)}/excel">DOWNLOAD EXCEL</a>
    </div>`;

  document.getElementById("status-select").value = deal.status;
  document.getElementById("save-status").addEventListener("click", async () => {
    const status = document.getElementById("status-select").value;
    await api("/api/deals/" + encodeURIComponent(deal.deal_id) + "/status", {
      method: "PATCH",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({status})
    });
    await loadDeals();
    await loadDeal(deal.deal_id);
  });
}

function derivedRows(derived) {
  const labels = {
    noi: "NOI",
    noi_basis: "NOI basis",
    cap_rate: "Cap rate",
    cap_rate_basis: "Cap rate basis",
    loan_amount: "Loan amount",
    initial_equity: "Initial equity",
    annual_debt_service: "Annual debt service",
    dscr: "DSCR",
    annual_cash_flow: "Annual cash flow",
    cash_on_cash: "Cash-on-cash",
    exit_value: "Exit value",
    irr: "IRR",
    equity_multiple: "Equity multiple"
  };
  const rows = Object.entries(derived);
  if (!rows.length) return "<p>No calculated outputs are currently available.</p>";
  return rows.map(([key, value]) => {
    const label = labels[key] || key.replaceAll("_", " ");
    const formatted = ["cap_rate", "cash_on_cash", "irr"].includes(key)
      ? formatPercent(value)
      : ["loan_amount", "initial_equity", "annual_debt_service", "annual_cash_flow", "exit_value", "equity_multiple", "dscr", "noi"].includes(key)
        ? formatNumber(value)
        : escapeHtml(value);
    return `<p><strong>${escapeHtml(label)}:</strong> ${formatted}</p>`;
  }).join("");
}

function formatNumber(value) {
  return value == null ? "Unavailable" : Number(value).toLocaleString(undefined, {maximumFractionDigits: 2});
}
function formatPercent(value) {
  return value == null ? "Unavailable" : (Number(value) * 100).toFixed(2) + "%";
}
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
}

loadDeals().catch(error => {
  pipeline.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
});
