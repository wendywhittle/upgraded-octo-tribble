# AletheiaTelos Architecture

## 1. Architectural Objective

AletheiaTelos is a decision-support system for institutional investment work.

The architecture exists to preserve four things:

1. **Evidence integrity**
2. **Analytical independence**
3. **Human authority**
4. **Institutional memory**

Everything else is implementation detail.

The system must remain understandable enough that a human can reconstruct how an analytical conclusion was produced and what happened after it.

---

## 2. System Shape

```text
                    OPPORTUNITY
                         │
                         ▼
                      EVIDENCE
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
      ASSET INTELLIGENCE      CAPITAL INTELLIGENCE
             │                       │
             └───────────┬───────────┘
                         ▼
             COMPUTATIONAL KALEIDOSCOPE
                         │
                         ▼
              CONFLICT / COEXISTENCE
                         │
                         ▼
               INDEPENDENT RISK
                  / SCENARIOS
                         │
                         ▼
                CONTRARIAN REVIEW
                         │
                         ▼
                  INVESTMENT CASE
                         │
                         ▼
               DECISION READINESS
                         │
                         ▼
                   DECISION GATE
                         │
                         ▼
                 HUMAN AUTHORITY
                         │
                         ▼
                 DECISION RECORD
                         │
                         ▼
                    OUTCOME
                         │
                         ▼
                    OBSERVER
                         │
                         ▼
                EPISTEMIC MEMORY
                         │
                         └──────► BETTER NEXT DECISION
```

This is a logical architecture, not a requirement that every box become a microservice.

**Prefer the simplest implementation that preserves the boundary.**

---

## 3. Canonical Objects

The architecture is organized around durable institutional objects, not agents.

### Opportunity

A candidate subject discovered through an authorized source or entered by a human.

Opportunity is not evidence.

### Evidence

A sourced, normalized, provenance-aware observation that can support analysis.

Evidence is not a decision.

### Analytical Perspective

A structured output from one independent reasoning lens.

A perspective is not authority.

### Scenario / Simulation

A defined analytical model exploring possible conditions and outcomes.

Simulation is not prediction.

### Investment Case

The assembled analytical package.

Investment Case is not authorization.

### Decision Readiness

A determination that the analytical package satisfies defined completeness and integrity conditions for human review.

Readiness is not approval.

### Decision Gate

The explicit boundary between analytical readiness and human authority.

### Decision Record

The durable historical record of the decision process and human decision.

The Decision Record is the authoritative historical record.

### Outcome / Observation

What actually happened after the decision.

### Epistemic Memory

Validated institutional learning derived from historical decisions and outcomes.

Memory does not rewrite the Decision Record.

---

## 4. Opportunity Acquisition Boundary

The acquisition path is:

```text
SOURCE
 ↓
ADAPTER
 ↓
RAW OBSERVATION
 ↓
NORMALIZATION
 ↓
DEDUPLICATION
 ↓
PROVENANCE
 ↓
OPPORTUNITY
 ↓
VALIDATION
```

Sources may be public, licensed, permitted, manually entered, or otherwise authorized.

The architecture must not assume unrestricted scraping.

A source can identify something worth investigating without establishing that it is true.

---

## 5. Evidence Boundary

Evidence enters through a controlled boundary.

Each material evidence item should preserve, where available:

- source
- retrieval time
- effective date
- subject
- raw representation
- normalized representation
- provenance
- freshness
- validation state
- corroboration state

The system must distinguish:

```text
OBSERVED
SUPPORTED
CALCULATED
ASSUMED
HYPOTHESIZED
PREDICTED
UNKNOWN
CONTRADICTED
UNAVAILABLE
```

These states must not be silently collapsed.

---

## 6. Asset Engine and Capital Engine

The engines are domain adapters over the same institutional intelligence discipline.

### Asset Engine

Handles real and private assets, including:

- property
- industrial
- NNN
- infrastructure
- development
- operations
- financing
- capital structure
- value creation

### Capital Engine

Handles financial and capital-market research, including:

- instruments
- markets
- quantitative research
- factors
- macro
- regimes
- alternative data
- risk
- portfolio research

Provider-specific integrations must remain behind adapters.

No vendor becomes the architecture.

---

## 7. Computational Kaleidoscope

The Kaleidoscope receives a common analytical question and common governed inputs.

Each perspective produces structured output.

Minimum conceptual contract:

```text
QUESTION
EVIDENCE
ASSUMPTIONS
ANALYSIS
SUPPORTING REASONS
COUNTER-EVIDENCE
UNCERTAINTY
CONDITIONS THAT WOULD CHANGE THE VIEW
```

Perspectives may include Research, Quant, Investor, Systems, Macro, Scientist, Contrarian, Governance, Observer, and Meta-Intelligence.

Independence means more than different labels.

Where practical, perspectives should have separable prompts, assumptions, calculations, or analytical methods so that disagreement carries information.

The system must preserve dissent.

---

## 8. Conflict / Coexistence

When perspectives disagree, the system asks why.

Possible causes include:

- different evidence
- different assumptions
- different time horizons
- different definitions
- different causal models
- different risk tolerances
- different regimes

The conflict layer must expose the disagreement rather than average it away.

Valid result:

**UNRESOLVED**

A system that cannot say "we do not know" is structurally unsafe for consequential analysis.

---

## 9. Independent Risk and Scenarios

Risk analysis is deliberately separated from thesis generation.

Core scenarios may include:

- BASE
- BULL
- BEAR
- ADVERSARIAL
- TAIL RISK

The risk system should expose:

- distributions
- sensitivity
- downside
- drawdown
- uncertainty
- assumption dependence
- model limitations

Where simulation is used, its parameters and outputs must be independently inspectable.

**SIMULATION ≠ PREDICTION**

The simulator does not inherit authority from an upstream agent.

---

## 10. Contrarian Review

The Contrarian layer actively searches for reasons the case should fail.

It should challenge:

- thesis assumptions
- evidence quality
- missing evidence
- asymmetric downside
- regime dependence
- liquidity
- financing
- structural fragility
- model risk
- implementation risk

Its purpose is not to be negative.

Its purpose is to prevent the system from treating a coherent story as proof.

---

## 11. Investment Case

The Investment Case is assembled from governed inputs:

```text
EVIDENCE
+
CALCULATIONS
+
ASSUMPTIONS
+
PERSPECTIVES
+
CONFLICT
+
RISK
+
CONTRARIAN REVIEW
+
UNRESOLVED QUESTIONS
```

Every material conclusion should be traceable to its underlying inputs where practical.

The Investment Case may contain a recommendation or NO ACTION.

It does not authorize execution.

---

## 12. Decision Readiness

Decision Readiness answers:

> Is the analytical package sufficiently complete and internally coherent to reach the human decision boundary?

It may consider:

- required evidence
- unresolved blockers
- calculation integrity
- scenario integrity
- independent review
- material contradictions
- missing information
- governance conditions

Readiness must be deterministic where the underlying checks are deterministic.

Readiness is not a prediction of what the human will decide.

---

## 13. Decision Gate

The Decision Gate is a hard architectural boundary.

```text
NOT READY
   │
   ├── insufficient evidence
   ├── material blocker
   ├── invalid analysis
   └── unresolved required condition

READY FOR HUMAN AUTHORITY
   ↓
HUMAN DECISION
```

The invariant is:

**RECOMMENDATION ≠ READINESS ≠ AUTHORIZATION ≠ EXECUTION**

No component downstream of the analytical stack may infer human authorization merely because readiness is true.

---

## 14. Human Authority and Execution

AletheiaTelos may support human-authorized execution workflows in the future, but authority must remain explicit.

The system does not autonomously:

- trade
- purchase
- sell
- transfer capital
- mutate portfolios
- sign legal agreements
- close transactions
- exercise investment authority

Technical connectivity is not permission.

Permission is not authority.

Authority is not execution.

---

## 15. Decision Record

The Decision Record is the durable historical object.

It should preserve:

- decision identity
- subject
- evidence references
- evidence state at decision time
- assumptions
- analytical perspectives
- conflicts
- simulation inputs and outputs
- contrarian objections
- Investment Case
- Decision Readiness state
- Decision Gate state
- human decision
- timestamps
- subsequent outcome references

History must be append-oriented.

A later outcome must not rewrite what the institution originally believed.

---

## 16. Outcome and Observer

After a decision, the system observes reality.

The Observer compares:

```text
THESIS
vs.
ASSUMPTIONS
vs.
EXPECTATIONS
vs.
REALITY
```

It should distinguish:

- forecast error
- assumption error
- evidence error
- execution effects
- external events
- model limitations
- attribution uncertainty

Outcome analysis must avoid hindsight rewriting.

---

## 17. Epistemic Memory

Epistemic Memory stores validated lessons from experience.

Memory may contain:

- resolved observations
- outcome relationships
- calibration information
- recurring failure patterns
- successful dissent
- validated lessons

Memory must preserve provenance and context.

Memory cannot:

- grant authority
- approve transactions
- silently modify historical decisions
- turn an uncertain belief into a fact

The learning loop is:

```text
DECISION
 ↓
OUTCOME
 ↓
OBSERVATION
 ↓
ATTRIBUTION
 ↓
MEMORY
 ↓
FUTURE ANALYSIS
```

---

## 18. Presentation Architecture

The website is a presentation layer over the canonical system.

It should expose real capabilities through a coherent experience:

```text
HOME
 ├── ASSET INTELLIGENCE
 ├── CAPITAL INTELLIGENCE
 ├── EVIDENCE
 ├── KALEIDOSCOPE
 ├── RISK / SCENARIOS
 ├── INVESTMENT CASE
 ├── DECISION GATE
 └── OUTCOMES / MEMORY
```

Pages are views into one system.

They are not separate sources of truth.

A UI element must never imply a backend capability that does not exist.

---

## 19. Runtime State

The interface must represent actual state.

At minimum:

- AVAILABLE
- NO DATA
- NOT AVAILABLE
- INSUFFICIENT EVIDENCE
- BLOCKED
- HOLD
- INVESTIGATE
- READY FOR HUMAN AUTHORITY

Do not fill missing state with fake metrics, invented activity, or decorative numbers.

---

## 20. Provider Independence

External services must be adapters.

The architecture should survive replacement of:

- model providers
- data providers
- memory providers
- orchestration frameworks
- databases
- cloud infrastructure
- browser/tool providers

External technology is replaceable implementation.

The institutional contracts are not.

---

## 21. Security and Least Privilege

Default posture:

```text
RESEARCH
  ↓
ANALYSIS
  ↓
HUMAN AUTHORITY
  ↓
AUTHORIZED EXECUTION
```

Credentials, tools, databases, external APIs, and execution capabilities require explicit scope.

Agents receive only the capabilities required for their role.

Consequential external actions require stronger controls than analysis.

---

## 22. Failure Philosophy

The system should fail visibly.

Prefer:

- unknown over invented
- incomplete over fabricated
- disagreement over false consensus
- blocked over unsafe continuation
- explicit limitation over hidden limitation
- reversible behavior over irreversible behavior

Failure states are part of the product.

---

## 23. Architectural Invariants

These are non-negotiable:

1. Canonical objects have one authoritative source.
2. Evidence is distinct from interpretation.
3. Assumptions are explicit.
4. Independent perspectives may disagree.
5. Simulation remains analytically distinct from prediction.
6. Readiness never becomes authorization.
7. Authorization never becomes autonomous execution.
8. Decision history is not rewritten by hindsight.
9. Memory does not become authority.
10. UI state reflects actual system state.
11. Missing data remains missing.
12. Provider integrations remain replaceable.
13. The simplest architecture that preserves these invariants is preferred.

---

## 24. Definition of Done

A feature is not complete because the page exists.

It is complete when:

```text
INPUT
 ↓
REAL PROCESSING
 ↓
CANONICAL STATE
 ↓
REAL OUTPUT
 ↓
VISIBLE STATE
 ↓
AUDITABLE HISTORY
```

The system should be able to demonstrate the complete path for a real analytical question.

**Do not build theater. Build the system.**
