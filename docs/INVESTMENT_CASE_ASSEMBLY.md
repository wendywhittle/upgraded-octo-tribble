# Investment Case Assembly

## Phase 9

Phase 9 establishes the smallest integration layer required to assemble the existing AletheiaTelos analytical outputs into one deterministic, auditable investment case.

It is an orchestration boundary, not a new analytical engine.

## Data flow

```text
DEAL
  ↓
PRO FORMA
  ↓
SCENARIOS
  ↓
SIMULATION
  ↓
CONTRARIAN
  ↓
CAPITAL STACK
  ↓
LENDER EVIDENCE
  ↓
INVESTMENT SYNTHESIS
  ↓
STRUCTURED INVESTMENT CASE
  ↓
HUMAN AUTHORIZATION
```

The assembly layer connects the existing engines and preserves their output classifications.

## Responsibilities

Phase 9 may:

- calculate a Pro Forma through the existing Pro Forma engine
- generate scenarios through the existing Scenario Engine
- invoke the existing CRE Simulation adapter and Monte Carlo engine
- run the existing Contrarian review
- calculate financing consequences through the existing Capital Stack engine when a capital stack is supplied
- carry structured lender profiles and financing terms with their provenance
- pass the assembled evidence and outputs into Investment Synthesis
- produce a single auditable envelope containing the resulting outputs
- expose conditional and insufficient-data states
- expose a recommendation without converting it into authorization

## Analytical boundaries

Each calculation remains authoritative in its originating engine:

- Pro Forma calculates property economics.
- Scenario Engine varies assumptions.
- Monte Carlo calculates distributions.
- Capital Stack calculates financing consequences.
- Contrarian interprets and challenges existing outputs.
- Investment Synthesis interprets the assembled evidence.
- Phase 9 assembles; it does not recalculate.

Lender-supplied financing terms remain evidence. Actual deal LTV, LTC, DSCR, debt yield, debt service, and related consequences remain Capital Stack calculations.

## Provenance

The assembly preserves the distinction between:

`FACT → SOURCE → ASSUMPTION → HYPOTHESIS → CALCULATION → INTERPRETATION → PREDICTION → RECOMMENDATION`

Calculation values are not rewritten as synthesis conclusions. Recommendations remain recommendations.

Lender evidence retains its source-derived provenance, freshness, verification, applicability, conditions, and conflict information.

## Contradiction and uncertainty

Contradictory evidence and unresolved questions are preserved in the assembled case. The assembly layer does not select a winning observation merely to produce a cleaner case.

Missing information may result in `CONDITIONAL` or `INSUFFICIENT_DATA` status. The system is allowed to recommend `NO_GO_RECOMMENDATION` when the available information does not justify proceeding.

A NO-GO recommendation does not mutate workflow state and does not constitute an investment authorization.

## Governance

The governing rule remains:

**AUTOMATION BETWEEN GATES. HUMAN AUTHORITY AT GATES.**

Phase 9 cannot:

- authorize underwriting, financing, or investment
- select or rank lenders
- deploy capital
- execute transactions
- contact or negotiate with lenders
- scrape external lender sources
- create a portfolio position
- create a new analytical engine
- create an investment score
- fabricate probabilities
- replace human authorization

The assembly output is a decision-support artifact. Workflow transitions and consequential authorization remain governed by `WorkflowService` and explicit human authorization.

## Relationship to Investment Synthesis

Investment Synthesis is responsible for structured interpretation of evidence and existing analytical outputs.

Phase 9 is responsible for connecting those outputs and packaging them into one auditable case.

Synthesis does not become an approval mechanism merely because Phase 9 consumes its output.

## Relationship to WorkflowService

Phase 9 does not mutate workflow state. `apply_assembly_to_case` returns a copied `InvestmentCase` envelope and leaves the original case unchanged.

Consequential workflow transitions remain separate and require the existing human authorization gates.

## Determinism

Assembly is deterministic for the same validated inputs and explicit simulation configuration. The existing Monte Carlo engine retains its explicit seed and path configuration.

Phase 9 introduces no web calls, LLM calls, hidden state, autonomous agents, or external execution.

## Future extension points

Future systems may add automated source collection, richer evidence ingestion, or additional workflow integration. Such systems should feed the existing evidence contracts rather than bypassing provenance and validation.

A future lender scraper belongs before structured lender ingestion, not inside Phase 9. A future lender matching layer should remain separate from analytical case assembly.
