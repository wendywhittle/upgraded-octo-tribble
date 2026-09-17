/*
 * Canonical dashboard renderer.
 * The machine-readable dashboard contract is the sole source for pipeline labels,
 * order, descriptions, and authority-safe navigation semantics.
 */
(async function loadCanonicalDashboardContract(){
  try {
    const response = await fetch("/web/dashboard-source-of-truth.json", {cache: "no-store"});
    if (!response.ok) throw new Error("Dashboard source-of-truth unavailable");
    const contract = await response.json();
    window.ALETHEIA_DASHBOARD_SOURCE_OF_TRUTH = contract;

    const canonicalStages = Array.isArray(contract.pipeline) ? contract.pipeline : [];
    const stageIcons = ["◎","▤","▦","◌","△","∿","◒","▣","◇","◉","✦"];
    const stageTargets = {
      opportunity: "active-analysis",
      evidence: "evidence",
      underwriting: "underwriting-workspace",
      perspectives: "perspective-summary",
      conflict: "conflict-intelligence",
      risk: "independent-risk",
      contrarian: "perspective-summary",
      investment_case: "investment-case",
      decision_gate: "decision-gate",
      observer: "observer",
      learning: "learning"
    };

    window.renderPipeline = function renderCanonicalPipeline(states={}) {
      const host = document.getElementById("pipeline-stages");
      if (!host) return;
      host.innerHTML = canonicalStages.map((stage, index) => {
        const state = states[stage.id] || {status: "NOT RUN", tone: ""};
        const target = stageTargets[stage.id] || "active-analysis";
        const icon = stageIcons[index] || "◇";
        const current = state.current ? " current" : "";
        return `<button class="stage${current}" data-target="${target}" data-canonical-stage="${stage.id}">
          <div class="stage-icon">${icon}</div>
          <div class="stage-num">${String(stage.number).padStart(2,"0")}</div>
          <div class="stage-name">${stage.label}</div>
          <div class="stage-status ${state.tone || ""}">${state.status || "NOT RUN"}</div>
          <div class="stage-desc">${stage.description}</div>
        </button>`;
      }).join("");
      host.querySelectorAll(".stage").forEach(button => {
        button.addEventListener("click", () => document.getElementById(button.dataset.target)?.scrollIntoView({behavior:"smooth", block:"start"}));
      });
    };

    if (canonicalStages.length === 11) {
      window.renderPipeline({
        opportunity:{status:"READY",tone:"good"},
        evidence:{status:"NOT RUN"},
        underwriting:{status:"INPUTS",tone:"warn"},
        perspectives:{status:"NOT RUN"},
        conflict:{status:"NO DATA"},
        risk:{status:"NOT RUN"},
        contrarian:{status:"NOT RUN"},
        investment_case:{status:"NOT RUN"},
        decision_gate:{status:"CLOSED"},
        observer:{status:"RECORDED",tone:"good"},
        learning:{status:"OUTCOME-DEPENDENT",tone:"warn"}
      });
    }
  } catch (error) {
    console.warn("AletheiaTelos canonical dashboard contract could not be loaded.", error);
  }
})();
