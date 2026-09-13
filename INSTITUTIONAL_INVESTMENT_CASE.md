# AletheiaTelos Institutional Investment Case Architecture

**Status:** Canonical Architectural Specification  
**Scope:** Architecture documentation only  
**Implementation Status:** Not yet implemented  
**Authority:** Subject to `CHARTER.md` and existing proprietary-system governance

---

## 1. Purpose

The **Institutional Investment Case** is the canonical analytical object that connects validated evidence and institutional reasoning to human decision authority, historical reconstruction, outcome attribution, and epistemic learning.

It exists because an institutional investment process cannot be represented adequately by a ticker, property, research report, model output, recommendation, or transaction alone. A durable institution must be able to reconstruct what it knew, what it believed, what it assumed, what it calculated, what challenged it, what remained uncertain, what alternatives existed, what humans decided, and what happened afterward.

The Investment Case therefore provides the common analytical container across the **Capital Engine** and **Asset Engine** while preserving their domain-specific requirements.

The Investment Case is designed to improve decision quality, not to manufacture activity or certainty.

---

## 2. Definition

An **Institutional Investment Case** is a versioned, evidence-linked, analytically assembled representation of an institutional investment question and the reasoning required to determine whether that question is sufficiently developed for human authority.

It may contain evidence, claims, assumptions, calculations, valuation, scenarios, simulations, risk analysis, competing perspectives, conflicts, contrarian review, uncertainty, decision options, governance conditions, and later outcome and attribution information.

The Investment Case is **not** an authorization mechanism and does not itself cause capital or asset movement.

### Distinctions

| Object | Meaning | Relationship to Investment Case |
|---|---|---|
| Opportunity | Something potentially worth investigating | Precursor / subject |
| Research Report | A research artifact or analysis of a subject | Contributing artifact |
| Underwriting | Domain-specific evaluation, especially for assets | Contributing analytical component |
| Financial Model | Mathematical representation of economics | Contributing calculation/model |
| Recommendation | An analytical conclusion or proposed course | Possible case output, never authority |
| Decision Readiness | Assessment that the case is sufficiently assembled for human review | State of the case |
| Decision Record | Durable record of the human decision and the case state at that time | Downstream governance artifact |
| Position | A capital-market holding | Possible downstream real-world state |
| Transaction | An authorized economic/legal event | Downstream execution state |
| Outcome | What subsequently happened | Downstream observation |

The Investment Case is therefore the **institutional analytical object between evidence and human authority**, while remaining connected to the complete lifecycle before and after the decision.

---

## 3. Case Identity

An Investment Case requires an identity independent of any external identifier.

A case identity must not be defined solely by:

- ticker
- company name
- property address
- provider identifier
- transaction identifier

Those identifiers are attributes associated with objects within a case. They are not the identity of the institutional case itself.

### Why multiple cases can exist

One company, security, property, project, borrower, issuer, or other economic subject may generate multiple Investment Cases because the institutional question, evidence state, market context, assumptions, capital structure, strategy, or decision context may change over time.

Examples include:

- the same security evaluated under different market regimes
- the same property evaluated for acquisition and later refinancing
- the same asset reconsidered after material new evidence
- the same issuer evaluated for different capital-allocation questions
- a prior case reopened as a new analytical case rather than rewritten retrospectively

### Temporal identity

A case therefore requires:

- stable case identity
- temporal case version
- creation context
- effective time/context
- evidence state associated with that version
- provenance of material changes

Historical versions must remain reconstructable.

A new case version may supersede a prior analytical state without rewriting the historical state that informed an earlier decision.

---

## 4. Lifecycle

The canonical lifecycle is:

```text
DISCOVERY
   ↓
CANDIDATE
   ↓
OPPORTUNITY
   ↓
CASE FORMATION
   ↓
EVIDENCE DEVELOPMENT
   ↓
ANALYSIS
   ↓
CASE ASSEMBLY
   ↓
DECISION READINESS
   ↓
HUMAN AUTHORITY
   ↓
DECISION RECORDED
   ↓
MONITORING
   ↓
REASSESSMENT
   ↓
DISPOSITION
   ↓
OUTCOME
   ↓
ATTRIBUTION
   ↓
MEMORY
   ↓
BETTER NEXT DECISION
```

Not every case reaches every state.

A case may terminate as `NO-GO`, `NO DEAL`, or `INSUFFICIENT EVIDENCE`. A case may never receive human authorization. A case may be authorized but never execute. A position or asset may remain open for an extended period before disposition. An outcome may remain pending or unknown.

The lifecycle is therefore a **stateful institutional process**, not a mandatory linear transaction workflow.

---

## 5. Constituents

| Constituent | Classification | Role |
|---|---|---|
| Investment Question | Required | Defines what the institution is trying to determine |
| Opportunity | Required | Defines the subject/context being evaluated |
| Identity | Required | Establishes what the case concerns |
| Thesis | Required for substantive evaluation | Defines the institutional interpretation being tested |
| Evidence | Required | Supports material claims and conclusions |
| Claims | Required | Expresses propositions derived from evidence and reasoning |
| Assumptions | Required where non-evidentiary inputs exist | Makes uncertainty and model inputs explicit |
| Calculations | Derived | Produces analytical quantities from inputs |
| Valuation | Optional by case type, required where valuation is material | Represents multiple valuation concepts without false precision |
| Scenarios | Required where uncertainty is material | Represents conditional futures |
| Simulation | Optional by case type, required where risk methodology calls for it | Produces conditional distributions |
| Risk | Required | Identifies material downside and uncertainty |
| Perspectives | Required for material institutional cases | Provides independent analytical lenses |
| Conflict / Coexistence | Required when disagreement exists | Preserves and analyzes dissent |
| Contrarian Review | Required for decision readiness | Challenges the case |
| Uncertainty | Required | Makes unknowns and limitations visible |
| Decision Readiness | Required before human-authority presentation | Determines analytical completeness |
| Decision Options | Required | Defines available analytical outcomes |
| Governance | Required | Applies authority and policy constraints |
| Human Decision | Downstream | Records human authority and decision |
| Outcome | Downstream | Records what subsequently happened |
| Attribution | Downstream | Evaluates outcome and process |

Optional or derived components must never be used to evade a material decision-readiness requirement.

---

## 6. Investment Question

The **Investment Question** is an explicit institutional statement of what the case is intended to determine.

Examples may include:

- Should the institution pursue this acquisition?
- Does the security warrant further research?
- Is the proposed valuation supported by available evidence?
- Should an existing holding be retained, reduced, or exited?
- Is a refinancing economically and risk-adjusted justified?

A case without a sufficiently defined question risks becoming an accumulation of disconnected analysis.

The Investment Question establishes the context against which evidence relevance, assumptions, scenarios, risks, and decision options can be evaluated.

---

## 7. Opportunity

An **Opportunity** is a candidate subject or situation that may warrant institutional investigation.

Opportunity remains distinct from the Investment Case.

```text
OPPORTUNITY
   ↓
QUESTION
   ↓
CASE FORMATION
   ↓
EVIDENCE + ANALYSIS
```

A listing, security symbol, market observation, lender indication, company disclosure, or other discovery artifact may identify an opportunity without establishing an Investment Case.

**Opportunity ≠ Evidence.**

An opportunity may be rejected before substantial case construction or may progress into a full institutional case.

---

## 8. Thesis

The **Thesis** is the institutional interpretation being tested by the Investment Case.

A thesis must remain traceable to:

- supporting evidence
- contradictory evidence
- assumptions
- causal or economic mechanisms
- expected outcomes
- risks
- invalidation conditions

A thesis is interpretation, not evidence.

The case should preserve both the thesis and the conditions under which the institution would conclude that the thesis is weakened, invalidated, or no longer applicable.

---

## 9. Evidence Linkage

Evidence enters the Investment Case through the Institutional Evidence Contract.

The canonical epistemic progression is:

```text
DISCOVERY
   ↓
RAW OBSERVATION
   ↓
IDENTITY
   ↓
EVIDENCE
   ↓
CLAIM
   ↓
ASSUMPTION
   ↓
CALCULATION
   ↓
SCENARIO
   ↓
SIMULATION
   ↓
INTERPRETATION
```

The Investment Case must preserve these distinctions:

- **DISCOVERY ≠ EVIDENCE**
- **RAW OBSERVATION ≠ VALIDATED EVIDENCE**
- **EVIDENCE ≠ CLAIM**
- **CLAIM ≠ INTERPRETATION**
- **CONFIDENCE ≠ PROVENANCE**
- **MISSING EVIDENCE ≠ NEGATIVE EVIDENCE**

Material conclusions should remain traceable to supporting evidence and/or explicitly declared assumptions.

Evidence should retain identity, source, location, observation/retrieval context, raw and normalized values, transformation history, validation status, freshness, and conflicts as required by the shared evidence architecture.

---

## 10. Asset Engine Underwriting

For the **Asset Engine**, the Investment Case may incorporate:

- CRE
- industrial
- NNN
- infrastructure
- private assets
- development
- operations
- financing
- capital structure
- value creation
- leasing and occupancy
- operating performance
- acquisition and disposition economics

Asset underwriting is therefore not merely a property calculator.

It is a structured examination of the economic asset, its operating reality, capital structure, financing conditions, value creation opportunities, risks, lifecycle, and potential disposition paths.

The Asset Engine contributes domain-specific analytical evidence and calculations to the common Investment Case while preserving the shared institutional governance boundary.

---

## 11. Capital Engine Analysis

For the **Capital Engine**, the Investment Case may incorporate:

- public markets
- securities and instruments
- quantitative research
- alternative data
- macroeconomic conditions
- factors
- market regimes
- valuation
- liquidity
- volatility
- correlation
- concentration
- portfolio context
- capital allocation research

Capital Engine analysis remains research and decision intelligence.

It must not become autonomous trading, portfolio mutation, capital transfer, or execution authority.

The Capital Engine and Asset Engine may differ substantially in their evidence and analytical methods while contributing to the same institutional case architecture.

---

## 12. Valuation

The Investment Case must distinguish among different meanings of value.

### Observed Market Value

A value directly observed from a relevant market observation or transaction context.

### Estimated Value

A value estimated from evidence, comparable observations, professional judgment, or other estimation methods.

### Model-Derived Value

A value produced by an explicit analytical model from stated inputs and assumptions.

### Scenario Value

A value conditional upon a defined scenario and its assumptions.

### Simulation Distribution

A distribution of conditional values generated through simulation across specified input uncertainty and scenario structures.

These concepts must not be collapsed into a single “true value.”

A model can be internally consistent while its assumptions are wrong. A market observation can be real while not representing the value relevant to the institutional question.

---

## 13. Assumptions

Assumptions are explicit analytical objects representing inputs that are not being treated as established evidence for the relevant case context.

They must be:

- visible
- attributable
- reviewable
- revisable
- historically preservable
- distinguishable from evidence

The architecture must preserve:

```text
EVIDENCE
   ≠
ASSUMPTION
   ≠
CALCULATION
   ≠
SCENARIO
   ≠
SIMULATION
```

Where an assumption materially affects the case, its impact should be visible through calculations, scenarios, sensitivities, or risk analysis where appropriate.

---

## 14. Scenarios

Scenarios are conditional analytical constructions describing how the case may behave under specified conditions.

The standard scenario vocabulary includes:

- **BASE**
- **BULL**
- **BEAR**
- **ADVERSARIAL**
- **TAIL / STRESS**

Scenarios are not predictions.

They are structured questions of the form:

> If these conditions and assumptions hold, what would the economics, risks, or outcomes look like?

Scenario definitions and their assumptions must remain historically attributable to the case version in which they were used.

---

## 15. Risk

Risk is a first-class component of the Investment Case.

Where applicable, the case may represent:

- market risk
- valuation risk
- liquidity risk
- leverage risk
- financing risk
- concentration risk
- operational risk
- regime risk
- model risk
- assumption risk
- tail risk
- execution risk
- data/evidence risk
- thesis invalidation risk

Risk analysis must be capable of challenging the attractiveness of the case rather than merely decorating a positive thesis.

Independent simulation and risk analysis remain analytically separate from human authority.

Risk identification does not authorize action, and the absence of an identified risk does not establish that no risk exists.

---

## 16. Computational Kaleidoscope

The Investment Case provides the institutional context for the **Computational Kaleidoscope**.

The Kaleidoscope is a structured computational environment in which multiple analytical perspectives examine the same institutional question and relevant case context.

Perspectives may examine:

- evidence
- assumptions
- causal mechanisms
- quantitative relationships
- system dependencies
- investment thesis
- failure modes
- epistemic limitations
- governance constraints

The Kaleidoscope is **not**:

- a collection of autonomous decision-makers
- a voting system
- institutional truth
- Investment Committee authority

Its purpose is to expose useful disagreement and improve analytical coverage.

**Agreement is not the objective. Better judgment is.**

---

## 17. Conflict / Coexistence

The Investment Case must represent disagreement rather than erase it.

Permitted states include:

- agreement
- disagreement
- unresolved conflict
- conditional agreement
- insufficient evidence

Conflict may arise from different:

- evidence sets
- assumptions
- time horizons
- market regimes
- causal models
- definitions of success
- risk interpretations

The system should identify why perspectives differ and what evidence could resolve the disagreement when resolution is possible.

Some conflicts should remain unresolved.

> **Dissent is information.**

Consensus must not be manufactured to make a case appear complete.

---

## 18. Contrarian Review

Contrarian Review is a deliberate challenge to the assembled case.

It should actively examine:

- thesis weakness
- disconfirming evidence
- hidden assumptions
- valuation fragility
- scenario dependence
- model structure
- hidden dependencies
- regime assumptions
- downside exposure
- thesis invalidation conditions
- evidence-quality problems

Contrarian Review may conclude that the case should not proceed to readiness.

It does not possess independent authority to approve or reject an investment. Its role is analytical challenge.

---

## 19. Decision Options

The Investment Case must support explicit analytical decision states.

At minimum:

- **INVESTIGATE**
- **NO-GO**
- **NO DEAL**
- **INSUFFICIENT EVIDENCE**
- **HOLD**
- **CONDITIONAL GO**
- **READY FOR HUMAN AUTHORITY**

Additional analytical states may be introduced where required, provided they do not blur the authority boundary.

### Additional useful distinctions

- **REASSESS**: existing case requires renewed analysis because conditions or evidence changed.
- **MONITOR**: case remains relevant but does not presently warrant escalation.
- **DISPOSITION REVIEW**: an existing holding or asset requires formal consideration of disposition.

These are analytical lifecycle states, not authorizations to execute transactions.

The vocabulary must preserve the difference between:

```text
ANALYTICAL STATE
      ≠
HUMAN DECISION
      ≠
AUTHORIZATION
      ≠
EXECUTION
```

---

## 20. Decision Readiness

A case may reach:

**OPEN — READY FOR HUMAN AUTHORITY**

only when the material requirements for institutional review have been satisfied.

Readiness should include, as applicable:

1. identity integrity
2. sufficient usable evidence
3. provenance for material evidence
4. material conflicts identified
5. assumptions documented
6. calculations reproducible
7. valuation structure present where material
8. scenarios present where material
9. independent risk analysis
10. contrarian review
11. uncertainty explicitly represented
12. decision options defined
13. case assembled coherently
14. governance requirements satisfied

Readiness is a determination about the completeness and integrity of the analytical package.

> **READY ≠ AUTHORIZED.**

A case may be ready and still receive `NO DEAL`, `NO-GO`, `HOLD`, or another human decision.

Missing material evidence must remain a blocker where the case cannot be responsibly evaluated without it.

---

## 21. Human Authority

Human authority is a hard architectural boundary.

AletheiaTelos may:

- prepare a case
- retrieve and evaluate evidence
- calculate
- simulate
- compare
- challenge
- identify conflicts
- identify risks
- determine analytical readiness

AletheiaTelos may not independently:

- authorize capital deployment
- approve an investment on behalf of an institution
- place trades
- transfer capital
- mutate portfolios
- execute contracts
- close transactions
- exercise legal or financial authority

The governing sequence remains:

```text
ANALYSIS
   ↓
DECISION READINESS
   ↓
HUMAN AUTHORITY
   ↓
AUTHORIZED EXECUTION
```

Automation may operate between gates. Human authority remains at consequential gates.

---

## 22. Decision Record

The **Decision Record** preserves the case state at the time of human decision.

It should preserve, as applicable:

- case identity and version
- Investment Question
- opportunity and identity
- evidence references and provenance
- material claims
- assumptions
- calculations
- valuation structures
- scenarios
- simulation results
- risk analysis
- perspectives
- conflict and coexistence
- contrarian review
- uncertainty
- decision options
- readiness state
- governance state
- human decision
- authorization context
- relevant timestamps

The Decision Record is not the same object as the Investment Case, but it references and freezes the relevant case context required to reconstruct the decision.

A later case revision must not rewrite the historical Decision Record.

---

## 23. Case Versioning

Case versions exist because institutional knowledge changes over time.

A version should preserve the relevant state of:

- evidence
- assumptions
- calculations
- scenarios
- perspectives
- conflicts
- risk
- readiness
- decision context

The architecture must support the question:

> **What did the institution know at the time?**

A fact discovered later must not retroactively become part of the earlier decision context.

A new case version may incorporate new evidence while preserving the prior version and its relationship to any Decision Record.

Historical reconstruction is a first-class requirement, not an audit afterthought.

---

## 24. Monitoring

An Investment Case can remain institutionally relevant after an initial decision.

Monitoring may detect:

- new evidence
- thesis drift
- assumption changes
- valuation changes
- risk changes
- regime changes
- operational changes
- financing changes
- market changes
- changes to invalidation conditions

Monitoring may trigger reassessment, but it must not silently mutate the historical case or decision context.

A material change should result in an attributable case update, reassessment, or new case version according to future implementation rules.

---

## 25. Disposition

**Disposition is a formal terminal boundary of the holding phase.**

It is not merely an “exit strategy” field.

For the Capital Engine, disposition may include:

- sell
- reduce
- close
- rebalance
- exit

For the Asset Engine, disposition may include:

- sale
- refinance
- recapitalization
- redevelopment transition
- asset transfer
- operating transition

Disposition must remain subject to human authority.

The institutional lifecycle is:

```text
HOLD / OPERATE
      ↓
DISPOSITION REVIEW
      ↓
HUMAN AUTHORITY
      ↓
AUTHORIZED DISPOSITION
      ↓
OUTCOME
      ↓
ATTRIBUTION
      ↓
EPISTEMIC MEMORY
```

The system may prepare disposition analysis and identify conditions, but it may not autonomously dispose of capital or assets.

---

## 26. Outcome

Outcome records what subsequently happened.

Possible outcome states include:

- realized
- unrealized
- partial
- failed
- unknown
- pending

Outcome must remain separate from decision quality.

A favorable outcome does not prove that the original process was sound.

An unfavorable outcome does not necessarily prove that the original decision was irrational.

The institution must evaluate process and outcome separately.

---

## 27. Attribution

Attribution examines the relationship between the original case and subsequent reality.

It may examine:

- what was expected
- what occurred
- which assumptions held
- which assumptions failed
- which evidence mattered
- which risks materialized
- which risks were missed
- which perspectives were useful
- which models failed
- which uncertainties mattered
- whether the decision process was sound

### Outcome Attribution

Outcome Attribution asks what contributed to the realized or observed result.

### Process Attribution

Process Attribution asks whether the institutional decision process was appropriately reasoned given the information available at the time.

These must not be collapsed into a single retrospective score.

Attribution must preserve the information available at the original decision point.

---

## 28. Epistemic Memory

Completed and materially evaluated cases may contribute to **Epistemic Memory**.

Memory may preserve:

- forecasts
- evidence
- assumptions
- rationale
- dissent
- scenarios
- simulations
- decisions
- outcomes
- attribution
- errors
- model failures
- process failures
- lessons

The learning relationship is:

```text
FORECAST
   ↓
RESOLUTION
   ↓
OBSERVER
   ↓
ATTRIBUTION
   ↓
EPISTEMIC MEMORY
   ↓
BETTER NEXT DECISION
```

Epistemic Memory is institutional history.

It is **not authority**.

It must never silently grant permission for future action, transform an old conclusion into a permanent truth, or override current evidence and governance.

The original Decision Record remains intact.

---

## 29. Shared Capital / Asset Model

The Investment Case is the shared institutional abstraction connecting the Capital Engine and Asset Engine.

```text
                 INSTITUTIONAL INVESTMENT CASE
                           /       \
                          /         \
                CAPITAL ENGINE   ASSET ENGINE
                     |                |
             domain-specific     domain-specific
              evidence and        evidence and
                analysis            analysis
                          \         /
                           \       /
                     SHARED INSTITUTIONAL
                        INTELLIGENCE
```

The common model preserves:

- Investment Question
- identity
- evidence
- claims
- assumptions
- calculations
- scenarios
- risk
- perspectives
- conflict
- contrarian review
- decision readiness
- human authority
- Decision Record
- monitoring
- disposition
- outcome
- attribution
- memory

Domain-specific structures remain necessary.

A CRE case should not be forced into a securities-only model. A securities case should not be forced into property underwriting. The common abstraction is institutional, not domain-naive.

---

## 30. Case Security

The Investment Case contains proprietary institutional reasoning and therefore must be protected as a first-class security boundary.

External systems may provide, where legally and contractually permitted:

- discovery
- raw observations
- market data
- filings
- alternative data
- reference information

External systems must not receive proprietary institutional material merely because they provide data.

The protected boundary includes:

- proprietary reasoning
- Investment Case deliberation
- Decision Records
- institutional memory
- perspective outputs
- internal risk conclusions
- Investment Committee deliberation
- strategy
- proprietary decision logic

The architecture remains provider-neutral.

External providers are source components, not institutional authorities.

The system boundary is conceptually:

```text
EXTERNAL SOURCE
      ↓
SOURCE ADAPTER
      ↓
RAW OBSERVATION
      ↓
NORMALIZATION
      ↓
EVIDENCE / VALIDATION
      ↓
ALETHEIA TELOS
      ↓
PROPRIETARY REASONING
      ↓
HUMAN AUTHORITY
```

The proprietary-system directive and Charter remain higher-order governance constraints.

---

## 31. Invariants

The following are architectural invariants:

- **Discovery ≠ Evidence**
- **Evidence ≠ Interpretation**
- **Interpretation ≠ Hypothesis**
- **Hypothesis ≠ Scenario**
- **Scenario ≠ Simulation**
- **Simulation ≠ Prediction**
- **Decision Readiness ≠ Authorization**
- **Authorization ≠ Execution**
- **Memory ≠ Authority**
- **Ticker ≠ Security Identity**
- **Issuer ≠ Instrument**
- **Company ≠ Security**
- **Agent ≠ Institutional Truth**
- **Recommendation ≠ Authorization**
- **Consensus ≠ Correctness**
- **Outcome ≠ Validation**
- **Automation ≠ Authority**
- **External Provider ≠ Institutional Truth**
- **Missing Evidence ≠ Negative Evidence**
- **NO-GO is a legitimate outcome**
- **NO DEAL is a legitimate outcome**
- **INSUFFICIENT EVIDENCE is a legitimate outcome**
- **A favorable outcome does not validate a flawed process**
- **An unfavorable outcome does not by itself invalidate a sound process**
- **A later-discovered fact must not rewrite earlier knowledge state**
- **Historical case state must remain reconstructable**
- **Dissent must not be erased for the appearance of consensus**
- **Technology does not define institutional architecture**
- **External data availability does not imply evidentiary sufficiency**
- **A case may be ready without being authorized**
- **A case may terminate without authorization or execution**
- **Disposition is a lifecycle boundary, not autonomous authority**
- **Epistemic Memory cannot authorize future action**

---

## 32. Testability

Future implementation must eventually be capable of demonstrating, at minimum:

1. The exact Investment Case presented for human authority can be reconstructed.
2. Evidence can be distinguished from assumptions.
3. Material claims can be traced to supporting evidence and/or explicit assumptions.
4. Discovery artifacts cannot silently become validated evidence.
5. Unresolved conflicts remain visible.
6. The case can show what was unknown at decision time.
7. Historical case versions can be preserved.
8. A later evidence update does not rewrite an earlier Decision Record.
9. READY can be distinguished from AUTHORIZED.
10. AUTHORIZED can be distinguished from EXECUTED.
11. Human authority remains explicit.
12. The original Decision Record remains immutable as historical context.
13. Monitoring can identify material change without silently rewriting history.
14. Disposition can connect to outcome, attribution, and memory.
15. Epistemic Memory cannot silently become authority.
16. Capital Engine and Asset Engine can use the same institutional case abstraction without losing domain-specific analytical requirements.
17. The case can represent `NO-GO`, `NO DEAL`, and `INSUFFICIENT EVIDENCE` without treating them as system failures.
18. Outcome Attribution and Process Attribution remain distinguishable.
19. Valuation types remain distinguishable rather than collapsing into one value.
20. Scenario analysis remains distinguishable from prediction.
21. Simulation remains distinguishable from prediction.
22. External provider records remain distinguishable from institutional evidence.
23. Proprietary reasoning does not cross unauthorized provider boundaries.
24. Case identity remains independent of ticker, address, provider ID, or transaction ID.

These are architectural acceptance criteria, not implementation requirements for the present documentation change.

---

# 33. Final Canonical Artifact

## A. Definition

A versioned, evidence-linked institutional analytical object that assembles the question, subject, evidence, reasoning, uncertainty, competing perspectives, risk, and decision-readiness context required for human investment authority and later institutional reconstruction.

## B. Conceptual Object Model

```text
INVESTMENT CASE
├── Case Identity
├── Case Version
├── Investment Question
├── Opportunity
├── Identity
├── Thesis
├── Evidence
│   └── Claims
├── Assumptions
├── Calculations
├── Valuation
├── Scenarios
├── Simulation
├── Risk
├── Perspectives
├── Conflict / Coexistence
├── Contrarian Review
├── Uncertainty
├── Decision Options
├── Decision Readiness
├── Governance
├── Human Decision [downstream]
├── Decision Record [downstream]
├── Monitoring [downstream]
├── Disposition [downstream]
├── Outcome [downstream]
├── Attribution [downstream]
└── Epistemic Memory [downstream]
```

## C. Lifecycle

```text
DISCOVERY
→ CANDIDATE
→ OPPORTUNITY
→ CASE FORMATION
→ EVIDENCE DEVELOPMENT
→ ANALYSIS
→ CASE ASSEMBLY
→ DECISION READINESS
→ HUMAN AUTHORITY
→ DECISION RECORDED
→ MONITORING
→ REASSESSMENT
→ DISPOSITION
→ OUTCOME
→ ATTRIBUTION
→ MEMORY
→ BETTER NEXT DECISION
```

Terminal or alternative paths are permitted, including `NO-GO`, `NO DEAL`, `INSUFFICIENT EVIDENCE`, `HOLD`, and abandonment before authorization.

## D. Required Constituents

At minimum, a substantive case requires a defined Investment Question, Opportunity/subject, Identity, material Evidence, Claims, applicable Assumptions, Risk, Uncertainty, Decision Options, Governance context, and sufficient analytical assembly to determine Decision Readiness.

Material cases require appropriate Perspectives, Conflict analysis where disagreement exists, and Contrarian Review before `OPEN — READY FOR HUMAN AUTHORITY`.

## E. Evidence Linkage

```text
DISCOVERY
→ RAW OBSERVATION
→ IDENTITY
→ EVIDENCE
→ CLAIM
→ INTERPRETATION
→ DECISION CASE
```

Provenance must remain distinct from confidence. Missing evidence must remain distinct from negative evidence.

## F. Decision-Readiness Requirements

A case may be `OPEN — READY FOR HUMAN AUTHORITY` only when identity, usable evidence, provenance, material conflicts, assumptions, calculations, applicable valuation/scenario structures, independent risk, contrarian review, uncertainty, decision options, case assembly, and governance requirements are sufficiently satisfied.

## G. Human Authority Boundary

```text
ANALYSIS
→ DECISION READINESS
→ HUMAN AUTHORITY
→ AUTHORIZED EXECUTION
```

The system may prepare and challenge the case. Human authority remains explicit.

## H. Versioning Model

Stable case identity plus immutable historical versions. New evidence may create a new analytical state without rewriting prior decision context.

## I. Monitoring / Disposition

Monitoring detects material change. Reassessment creates attributable new analytical context. Disposition formally ends the holding phase and remains subject to human authority.

## J. Outcome / Attribution

Outcome records what happened. Attribution evaluates both outcome contribution and process quality. Neither is permitted to rewrite the historical decision state.

## K. Epistemic Memory Relationship

```text
CASE
→ DECISION
→ OUTCOME
→ OBSERVATION
→ ATTRIBUTION
→ EPISTEMIC MEMORY
→ BETTER NEXT DECISION
```

Memory is institutional history, not authority.

## L. Capital / Asset Compatibility

Capital Engine and Asset Engine share the same institutional case architecture while retaining domain-specific evidence, calculations, risk structures, valuation methods, and operating context.

## M. Security Boundary

External providers feed discovery and evidence acquisition where authorized. Proprietary reasoning, deliberation, Decision Records, institutional memory, internal risk conclusions, strategy, and decision logic remain inside the institutional boundary.

## N. Invariants

The Investment Case must preserve the epistemic, governance, identity, authority, historical, and security invariants established throughout this specification and the governing Charter.

## O. Unresolved Questions

The following remain intentionally open for later architectural work and must not be prematurely resolved by implementation convenience:

1. Exact persistent representation of case identity and version lineage.
2. Exact relationship between Investment Case versions and Decision Record versions.
3. Criteria for opening a new case versus creating a new version of an existing case.
4. Domain-specific minimum evidence thresholds for Capital Engine and Asset Engine cases.
5. Exact conflict-resolution and coexistence representation.
6. Exact monitoring-trigger and reassessment semantics.
7. Exact disposition state machine for different asset and capital classes.
8. Exact attribution methodology and evaluation periods.
9. Future retention and archival policy.
10. Future authorization and governance workflow details.
11. Future implementation of conceptual testability requirements.
12. Future provider/source adapters and their evidentiary authority by source type.

These questions are deliberately left open. No provider, package, database, framework, or infrastructure component is permitted to define the answer by default.

---

## Architectural Status

This document establishes the **Institutional Investment Case as a canonical architectural concept** for AletheiaTelos.

It does not implement the concept.

It does not create runtime behavior.

It does not establish a database schema.

It does not select a provider.

It does not authorize capital movement, trading, transaction execution, or disposition.

The governing principle remains:

> **Technology must conform to the architecture. The architecture must not be distorted to accommodate technology.**

The Investment Case exists to make institutional reasoning reconstructable while preserving evidence integrity, uncertainty, dissent, human authority, capital preservation, and proprietary protection.
