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
  detail.classList.remove("hidden");
  detail.innerHTML = `
    <div class="section-head"><p class="eyebrow">DEAL RECORD</p><h2>${escapeHtml(deal.deal_id)}</h2><p>${escapeHtml(deal.original_inputs?.name || "")}</p></div>
    <div class="record"><p><strong>Asset:</strong> ${escapeHtml(deal.original_inputs?.asset_type || "Unavailable")}</p><p><strong>Location:</strong> ${escapeHtml(deal.original_inputs?.location || "Unavailable")}</p><p><strong>Purchase price:</strong> ${formatNumber(deal.original_inputs?.purchase_price)}</p><p><strong>NOI:</strong> ${formatNumber(deal.underwriting?.noi)}</p><p><strong>Cap rate:</strong> ${formatPercent(deal.underwriting?.cap_rate)}</p><p><strong>Status:</strong> ${escapeHtml(deal.status)}</p></div>
    <div class="record"><label>Pipeline status <select id="status-select"><option>NEW</option><option>REVIEWING</option><option>PURSUE</option><option>HOLD</option><option>PASS</option></select></label><button id="save-status" class="primary" type="button">SAVE STATUS</button><a class="nav-button" href="/api/deals/${encodeURIComponent(deal.deal_id)}/excel">DOWNLOAD EXCEL</a></div>`;
  document.getElementById("status-select").value = deal.status;
  document.getElementById("save-status").addEventListener("click", async () => {
    const status = document.getElementById("status-select").value;
    await api("/api/deals/" + encodeURIComponent(deal.deal_id) + "/status", {method:"PATCH", headers:{"Content-Type":"application/json"}, body:JSON.stringify({status})});
    await loadDeals();
    await loadDeal(deal.deal_id);
  });
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
