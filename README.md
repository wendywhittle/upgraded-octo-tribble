# Institutional Intelligence Engine

## Capital + Real Assets

**Institutional commercial real estate is the initial application.**

This project evolves the AletheiaTelos research into an institutional intelligence engine designed to improve how difficult capital and real-asset questions are researched, challenged, simulated, decided, and learned from over time.

It is a **research and decision-intelligence system, not an autonomous investment system**. Human investment authority remains explicit.

## The Principle

> **The system should earn the right to act.**

The system is not optimized for activity, forced consensus, or a single confident answer. **ACT, WATCH, REJECT, INSUFFICIENT EVIDENCE, NO TRADE, and NO DEAL** are all valid outcomes.

## Computational Kaleidoscope

A question can be examined through independently inspectable perspectives:

- Researcher
- Quant
- Underwriter
- Investor
- Macro
- Systems
- Scientist
- Contrarian
- Risk
- Philosopher
- Observer
- Epistemic Memory

For CRE, `app/cre_kaleidoscope.py` provides typed assessment records for Underwriter, Investor, Quant, Researcher, Macro, Systems, Contrarian, and Risk. These are an adapter into the existing Computational Kaleidoscope, not a second autonomous agent framework.

The purpose is not to create more agents for their own sake. It is to create genuinely different ways of seeing the same question.

## Conflict Before Consensus

Conflicting conclusions are preserved rather than averaged into a meaningless signal.

The system asks:

**WHY DO THEY DISAGREE?**

Conflict analysis considers direction, confidence, time horizon, evidence, contradictory evidence, assumptions, regime, correlation, liquidity, risk, capacity, and invalidation conditions.

## Decision Pipeline

```text
REAL WORLD
    ↓
OPPORTUNITY
    ↓
EVIDENCE
    ↓
MULTI-PERSPECTIVE REASONING
    ↓
CONFLICT
    ↓
SIMULATION
    ↓
ADVERSARIAL REVIEW
    ↓
DECISION
    ↓
HUMAN AUTHORITY
    ↓
CAPITAL / ASSET
    ↓
OBSERVE OUTCOME
    ↓
EPISTEMIC MEMORY
    ↓
NEXT OPPORTUNITY
```

## Independent Simulation

The risk engine is designed to test assumptions independently through scenario distributions rather than relying on a single predicted outcome. The CRE boundary in `app/cre_simulation.py` preserves explicit underwriting variables and missing values before they reach an independent simulator. Scenario contracts in `app/cre_scenarios.py` support Base, Bull, Bear, Adversarial, and Tail Risk without fabricating CRE assumptions.

Agents may supply assumptions. The simulator remains independently inspectable and its outputs are reviewable by Contrarian and Risk perspectives.

## Commercial Real Estate

CRE is the first real-world application. Typed contracts now separate the core concerns:

- `app/cre_intelligence.py` — conservative opportunity screening
- `app/cre_underwriting.py` — property, assumption, underwriting, and decision contracts
- `app/cre_kaleidoscope.py` — structured multi-perspective CRE assessments
- `app/cre_scenarios.py` — scenario/risk contracts
- `app/cre_simulation.py` — explicit underwriting-to-simulation boundary
- `app/cre_decision.py` — auditable decision record with human authority preserved
- `app/cre_workflow.py` — ordered workflow boundaries

The institutional intelligence path is:

```text
OPPORTUNITY
→ SCREENING
→ UNDERWRITING
→ DUE DILIGENCE
→ SCENARIO ANALYSIS
→ CAPITAL STRUCTURE
→ VALUE CREATION
→ INVESTMENT COMMITTEE
→ CAPITAL / ASSET
→ OBSERVE OUTCOME
→ EPISTEMIC MEMORY
```

Underwriting is assumption-driven and evidence-aware. Missing required inputs produce **INSUFFICIENT EVIDENCE** rather than invented numbers. Explicit, evidence-supported failure conditions can produce **NO DEAL**. Neither state authorizes investment activity.

## Institutional Memory

The long-term objective is not a document dump. It is compounding institutional context:

```text
WHAT WE BELIEVED
        ↓
WHY WE BELIEVED IT
        ↓
WHAT WE DECIDED
        ↓
WHAT HAPPENED
        ↓
WHERE REASONING WAS WRONG
        ↓
WHAT CHANGED
        ↓
WHAT WE NOW BELIEVE
```

## Capital Intelligence

Capital intelligence focuses on:

- Risk
- Exposure
- Liquidity
- Correlation
- Capacity
- Regime
- Drawdown
- Scenario distributions
- Margin of safety
- Capital preservation
- Opportunity cost

The objective is decision quality, not forced deployment.

## Governance

The system constitution is defined in [`CHARTER.md`](CHARTER.md). It establishes boundaries around human authority, tools, persistence, memory, self-modification, execution, risk controls, auditability, independent oversight, model changes, data integrity, and secrets.

The Computational Kaleidoscope is a multi-perspective reasoning and observability layer. It does not grant investment authority, and its read-only projection explicitly preserves the execution boundary.

## Architecture Direction

The existing AletheiaTelos prototype is treated as a research seed. Valuable components can be preserved and refactored; obsolete components can be removed; new components are added only when they improve intelligence, discipline, auditability, or learning.

The target is a simple, inspectable architecture rather than complexity for its own sake.

## Institutional Learning Loop

**INTELLIGENCE → DISCIPLINE → DECISION QUALITY → OBSERVATION → LEARNING → COMPOUNDING INSTITUTIONAL KNOWLEDGE**
