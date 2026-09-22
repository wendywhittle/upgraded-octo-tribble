const login = document.getElementById("login");
const app = document.getElementById("app");
const form = document.getElementById("login-form");
const error = document.getElementById("login-error");
const pipeline = document.getElementById("pipeline-list");
const detail = document.getElementById("detail");
const logout = document.getElementById("logout");

async function api(url, options = {}) {
  const response = await fetch(url, { credentials: "same-origin", ...options });
  if (!response.ok) {
    let message = "Request failed";
    try { message = (await response.json()).detail || message; } catch {}
    throw new Error(message);
  }
  return response;
}

function showWorkspace() {
  login.classList.add("hidden");
  app.classList.remove("hidden");
}

function showLogin(message = "") {
  app.classList.add("hidden");
  login.classList.remove("hidden");
  error.textContent = message;
  error.classList.toggle("hidden", !message);
}

async function checkSession() {
  try {
    await api("/internal/session");
    showWorkspace();
    await loadDeals();
  } catch {
    showLogin();
  }
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

form.addEventListener("submit", async event => {
  event.preventDefault();
  error.classList.add("hidden");
  const accessKey = String(new FormData(form).get("access_key") || "").trim();
  try {
    const response = await api("/internal/login", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({access_key: accessKey})});
    if (!response.ok) throw new Error("Access denied");
    form.reset();
    showWorkspace();
    await loadDeals();
  } catch (err) {
    showLogin(err.message);
  }
});

logout.addEventListener("click", async () => {
  try { await api("/internal/logout", {method:"POST"}); } finally { showLogin(); }
});

checkSession();
