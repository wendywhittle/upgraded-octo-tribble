# AletheiaTelos Architecture Assessment

## Scope

Assessment of the existing `main` architecture before the institutional CRE workflow migration. The assessment preserves the existing intelligence stack and adds a workflow spine around it.

## Current → Target Map

| Current component | Current responsibility | Target responsibility | Action | Dependencies / risks |
|---|---|---|---|---|
| `CHARTER.md` | Constitutional governance, human authority, evidence/provenance, memory, security boundaries | Constitutional boundary | KEEP | Must remain authoritative; no workflow may weaken it |
| `app/agent_contract.py`, `agent_registry.py`, `agent_runner.py` | Agent contracts, registration, execution/provider boundary | Reasoning layer | KEEP | Agents must remain non-authoritative for gates and deterministic calculations |
| `app/evidence.py`, `evidence_pipeline.py`, `evidence_orchestration.py`, `evidence_sources.py` | Evidence collection, provenance, orchestration | Intelligence/evidence layer feeding deals and cases | KEEP / EXTEND LATER | Avoid creating a second evidence system |
| `app/analysis_pipeline.py` | Multi-perspective analysis, conflict detection, synthesis | Intelligence pipeline invoked by workflow stages | KEEP / ADAPT LATER | Workflow should orchestrate it rather than duplicate it |
| `app/conflict_intelligence.py` | Conflict/coexistence analysis | Disagreement layer | KEEP | Dissent must remain inspectable |
| `app/simulator.py` | Independent stochastic simulation with reproducibility | Simulation engine for CRE cases | KEEP / ADAPT LATER | Preserve seed/reproducibility and independence from agents |
| `app/skeptic.py` | Adversarial/skeptic review | CRE Contrarian layer | KEEP / EVOLVE LATER | Do not create a duplicate adversarial engine |
| `app/meta_intelligence.py` | Reasoning-process evaluation | Meta-intelligence layer | KEEP | Remains separate from authorization |
| `app/observer.py`, `learning.py`, `memory.py`, prediction resolution | Observation, learning, append-only institutional memory, prediction outcomes | Observer / outcome / epistemic memory | KEEP / EXTEND LATER | Preserve original decisions rather than overwrite them |
| `app/schemas.py` | Existing evidence, agent, conflict, simulation contracts | Existing analytical contracts plus future CRE contracts | MODIFY LATER | New workflow contracts should not destabilize existing schemas |
| `app/main.py` | FastAPI composition and legacy compatibility routes | Application boundary and workflow API composition | MODIFY | UI/API must call domain services, not own authority |
| `web/`, `index.html`, `simulator.html` | Existing dashboard/control views | Human control plane | MODIFY LATER | Do not move business authority into frontend state |
| `render.yaml`, CI | Deployment and test runtime | Same application runtime | KEEP | No microservice split justified by Phase 1 |
| `tests/` | Existing regression/governance/evidence/simulation/learning tests | Regression + workflow governance tests | EXTEND | Existing suite remains a contract |
| Persistence via `app/memory.py` | Append-only JSONL epistemic memory | Existing memory plus workflow event persistence | EXTEND | A small JSONL event store is sufficient for the first slice |
| Existing workflow/state | No persistent CRE authorization state machine found | Explicit workflow spine | ADD | Must enforce transitions server/domain side |
| Existing authorization | Governance flags/human decision requirements, but no CRE gate object/state machine | Explicit Authorization domain events | ADD | Must not infer authorization from model output or UI |
| Investment/portfolio domain | No persistent CRE portfolio workflow layer found | InvestmentCase and Portfolio domains | ADD LATER | Do not implement in Phase 1 |

## Architectural Finding

The repository is not a blank prototype. It already has a meaningful intelligence, evidence, simulation, governance, observation, and learning substrate. The missing layer is a persistent institutional workflow spine connecting those capabilities to explicit CRE deal lifecycle states and human authorization gates.

## Phase 1 Decision

Add four tightly related capabilities:

1. Domain objects for Opportunity, Deal, Authorization, InvestmentCase, and AuditEvent.
2. A backend workflow state machine with explicit allowed transitions.
3. Human authorization gates for underwriting, capital structure, and investment approval.
4. Append-only JSONL workflow audit persistence.

No new database, broker, microservice, agent layer, or dashboard rewrite is required for this slice.

## Authority Boundary

The workflow service rejects agent-authored state mutation and rejects gate transitions without a matching human approval bound to the current deal object version. The frontend is therefore a consumer of the domain boundary rather than the authority boundary.

## Next Slice

After the workflow foundation is verified, build the deterministic CRE Pro Forma Engine as a separate computational domain. The existing simulator and skeptic should then be adapted to consume structured CRE outputs rather than replaced.
