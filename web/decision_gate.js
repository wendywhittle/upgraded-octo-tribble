(() => {
  const $ = id => document.getElementById(id);
  let previousState = null;

  const labels = {
    OPPORTUNITY_DEFINED: "OPPORTUNITY",
    EVIDENCE_INTEGRITY: "EVIDENCE",
    UNDERWRITING_COMPLETE: "UNDERWRITING",
    MULTI_PERSPECTIVE_CHALLENGE_COMPLETE: "CHALLENGE",
    CONTRARIAN_REVIEW_COMPLETE: "CONTRARIAN",
    SCENARIO_ANALYSIS_COMPLETE: "SCENARIOS",
    CONFLICTS_CHARACTERIZED: "CONFLICTS",
    MATERIAL_UNKNOWNS_CLASSIFIED: "UNKNOWNS",
    GOVERNANCE_CHECK_PASSED: "GOVERNANCE",
    DECISION_RECORD_COMPLETE: "RECORD",
  };

  function esc(value) {
    return String(value ?? "").replace(/[&<>\"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
  }

  function render(result) {
    const criteria = result?.readiness_criteria || {};
    $("gate-system-status").textContent = result?.state === "OPEN" ? "READY FOR HUMAN AUTHORITY" : "READINESS BLOCKED";
    $("gate-criteria").innerHTML = Object.entries(labels).map(([key, label]) => {
      const status = criteria[key] || "FAIL";
      return `<div class="gate-criterion ${status === "PASS" ? "pass" : "fail"}"><span>${label}</span><strong>${status}</strong></div>`;
    }).join("");

    const open = result?.state === "OPEN";
    const seal = $("gate-seal");
    seal.className = `gate-seal ${open ? "open" : "closed"}`;
    seal.querySelector("strong").textContent = open ? "OPEN" : "CLOSED";
    seal.querySelector("em").textContent = open ? "READY FOR HUMAN AUTHORITY" : "NOT READY";

    $("gate-recommendation").textContent = result?.system_recommendation || "NOT AVAILABLE";
    const blockers = result?.hard_stops || [];
    $("gate-blockers").innerHTML = open
      ? "ANALYSIS COMPLETE ENOUGH FOR HUMAN JUDGMENT. THIS IS NOT APPROVAL."
      : `<span>BLOCKING CONDITIONS</span>${blockers.length ? blockers.map(x => `<strong>${esc(x)}</strong>`).join("") : "<strong>READINESS CRITERIA INCOMPLETE</strong>"}`;

    $("gate-actions").hidden = !open;
    previousState = result?.state || null;
  }

  async function evaluate(analysis) {
    try {
      const response = await window.__aletheiaOriginalFetch("/decision-gate/evaluate", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({analysis, previous_state: previousState}),
      });
      if (!response.ok) throw new Error("Decision Gate evaluation failed");
      const result = await response.json();
      render(result);
      return result;
    } catch (error) {
      $("gate-system-status").textContent = "GATE EVALUATION UNAVAILABLE";
      $("gate-blockers").textContent = error.message;
      return null;
    }
  }

  async function recordHumanDecision(disposition) {
    const rationale = window.prompt(`RATIONALE FOR HUMAN DECISION: ${disposition}`);
    if (!rationale || !rationale.trim()) return;
    const response = await window.__aletheiaOriginalFetch("/decision-gate/record-decision", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({gate_state: previousState || "OPEN", disposition, rationale: rationale.trim(), exception_acknowledged: false}),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      window.alert(data.detail || "Human decision could not be recorded.");
      return;
    }
    const record = await response.json();
    $("gate-human-decision").textContent = record.human_decision;
    $("gate-rationale").textContent = record.human_rationale;
  }

  document.addEventListener("click", event => {
    const button = event.target.closest("#gate-actions [data-disposition]");
    if (button) recordHumanDecision(button.dataset.disposition);
  });

  // app.js owns the analysis workflow. Intercept only its completed analysis response
  // so the governance layer evaluates the server result without duplicating the pipeline.
  window.__aletheiaOriginalFetch = window.fetch.bind(window);
  window.fetch = async (...args) => {
    const response = await window.__aletheiaOriginalFetch(...args);
    const url = typeof args[0] === "string" ? args[0] : args[0]?.url;
    if (url && url.endsWith("/analysis/run") && response.ok) {
      const clone = response.clone();
      clone.json().then(analysis => evaluate(analysis)).catch(() => {});
    }
    return response;
  };

  render({state: "CLOSED", readiness_criteria: {}, hard_stops: [], system_recommendation: null});
})();
