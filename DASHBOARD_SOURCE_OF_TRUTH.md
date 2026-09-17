# AletheiaTelos Interactive Dashboard Platform
## Canonical Source of Truth

**Status: CANONICAL / PIXEL-FAITHFUL REFERENCE**

The supplied AletheiaTelos dashboard screenshot is the **master visual reference** for the interactive dashboard platform. Future dashboard implementation must reproduce its composition, proportions, density, hierarchy, styling, navigation, status treatment, panel geometry, and interaction language as closely as the responsive viewport permits.

This is not merely inspiration and is not a loose design direction. It is the canonical workstation presentation that subsequent dashboard work must implement.

### Normative artifacts

1. `docs/dashboard/aletheia-telos-interactive-dashboard-source-of-truth.jpg` — the visual master supplied by the system owner.
2. `web/dashboard-source-of-truth.json` — the machine-readable platform contract.
3. This document — the human-readable implementation contract.
4. `web/styles.css` — the production visual implementation of the canonical reference.

If another dashboard mockup, screenshot, component arrangement, styling direction, or generic UI convention conflicts with these artifacts, these artifacts control unless a later, explicitly governed dashboard source-of-truth replaces them.

## 1. Platform identity

The dashboard is the **AletheiaTelos Institutional Intelligence System**.

Required identity language:

- **ALETHEIA TELOS**
- **INSTITUTIONAL INTELLIGENCE SYSTEM**
- **RESEARCH ONLY SYSTEM**
- **Truth-Seeking. Evidence-Grounded. Human-Governed.**

The dashboard must communicate an institutional research workstation, not a trading terminal, consumer analytics product, CRE listing portal, or autonomous investment agent.

## 2. Canonical visual implementation rule

The supplied screenshot is the visual master. Implementations must preserve, rather than reinterpret, the following characteristics:

- fixed institutional left navigation with compact spacing
- compact top system bar with status chips and command controls
- dense horizontal 11-stage pipeline with directional progression
- compact card-based analytical workspace
- right-side institutional rail
- dark navy/black terminal background
- thin blue-green structural borders
- cyan system accents
- violet analytical accents
- green operational/completion states
- amber warning/uncertainty states
- red downside/adversarial states
- compact monospaced information typography
- small uppercase section labels
- restrained glow and scanline treatment
- dense information presentation with minimal wasted space
- persistent human-authority boundary

**Pixel-faithful means the page should visually read as the same workstation shown in the reference image, not merely as another dark dashboard.**

Responsive behavior may reflow the composition for smaller screens, but must preserve the same visual system and hierarchy. Responsive adaptation must not become a separate design language.

## 3. Canonical information architecture

The dashboard is organized around a persistent institutional workstation:

- left navigation for system/workspace domains
- top system status and command area
- horizontal investment-intelligence pipeline
- active analysis workspace
- competing-perspective workspace
- decision-gate state
- independent-risk workspace
- conflict intelligence
- learning and calibration
- observation/recent activity
- right institutional rail
- persistent human-authority boundary

The interface is interactive. Panels represent actual system state and should be data-bound wherever the backend exposes the corresponding state.

## 4. Canonical 11-stage pipeline

The visible pipeline is fixed to the following institutional sequence:

| # | Stage | Description |
|---|---|---|
| 1 | OPPORTUNITY | Acquisition & Normalization |
| 2 | EVIDENCE | Collection & Validation |
| 3 | UNDERWRITING | Calculation & Analysis |
| 4 | PERSPECTIVES | Computational Kaleidoscope |
| 5 | CONFLICT | Intelligence & Synthesis |
| 6 | INDEPENDENT RISK | Monte Carlo Simulation |
| 7 | CONTRARIAN | Skeptic & Adversary Review |
| 8 | INVESTMENT CASE | Synthesis & Documentation |
| 9 | DECISION GATE | Readiness & Governance |
| 10 | OBSERVER | Record & Monitor |
| 11 | LEARNING | Calibration & Improvement |

The pipeline is not decorative. Each stage is an interactive entry point into the corresponding analytical or institutional boundary.

The stage ordering must not be silently changed by a UI redesign.

## 5. Canonical dashboard regions

### Active Analysis

Shows the current investment question/opportunity and the state of the analytical process.

### Perspective Summary

Shows competing outputs from the Computational Kaleidoscope. The UI must preserve differentiated perspectives and must not manufacture consensus.

### Decision Gate Status

Shows whether the analytical prerequisites are satisfied for human review.

**READY FOR HUMAN AUTHORITY is not authorization.**

### Independent Risk Summary

Shows independently generated scenario analysis. Agent conclusions must not be used as the simulation result.

The system may display scenarios such as Base, Bull, Bear, Adversarial, and Tail/Stress where supported by the implementation.

### Conflict Intelligence

Surfaces unresolved disagreement, conflicting assumptions, horizon divergence, and other material analytical conflicts.

Conflict must remain visible rather than being averaged away.

### Learning & Calibration

Shows outcome-dependent learning and calibration only when supported by actual records. The UI must not fabricate learning, calibration, or historical outcomes.

### Observer / Recent Activity

Shows durable observations and recent system events represented by actual records.

### Right Institutional Rail

The canonical right rail contains:

1. Create New Analysis
2. Recent Analyses
3. System Status
4. Human Authority Boundary

The Human Authority Boundary is permanent platform language.

## 6. Human authority boundary

> AletheiaTelos provides research, analysis, simulation and decision intelligence.

> It does not authorize, execute, trade, transfer capital, or mutate portfolios.

> All investment decisions require human authority and accountability.

No visual element may imply that analytical readiness is equivalent to authorization or execution.

## 7. Interaction rules

The dashboard should support:

- creation of a new analysis
- navigation through pipeline stages
- inspection of returned perspectives
- inspection of independent simulation results
- inspection of conflicts
- inspection of decision readiness/gate state
- inspection of recent analyses and institutional memory
- access to learning/calibration when data exists

The dashboard must not introduce:

- autonomous trade execution
- brokerage connectivity
- capital transfer
- portfolio mutation
- autonomous investment approval
- hidden authority through UI controls

## 8. Architecture relationship

The dashboard is the interactive presentation and control surface for the existing AletheiaTelos architecture. It does not become a new authority layer.

The canonical conceptual flow remains:

`CAPITAL ENGINE + ASSET ENGINE → OPPORTUNITY → EVIDENCE → UNDERWRITING / ANALYSIS → COMPUTATIONAL KALEIDOSCOPE → CONFLICT / COEXISTENCE → INDEPENDENT RISK SIMULATION → CONTRARIAN REVIEW → DECISION GATE → HUMAN INVESTMENT AUTHORITY → DECISION RECORD → OUTCOME → OBSERVATION → EPISTEMIC MEMORY → BETTER NEXT DECISION`

The dashboard must expose this architecture rather than replace it.

## 9. Implementation rule

Future dashboard work must start from this source of truth and the supplied screenshot.

Do not create a competing dashboard concept, alternate primary pipeline, decorative mockup, or disconnected UI architecture without an explicit replacement of this source-of-truth contract.

Do not progressively simplify the visual design into generic cards, large whitespace layouts, generic SaaS navigation, chat-first interfaces, or consumer-finance patterns.

Backend capability remains authoritative for values and state. This source of truth is authoritative for the dashboard's information architecture, interaction model, visual language, and institutional boundary presentation.

**Automation discovers. Evidence validates. Intelligence analyzes. The system challenges itself. Humans authorize.**
