# Capital Stack / Financing Intelligence Foundation

## 1. Purpose

The Capital Stack layer represents a proposed CRE financing structure and calculates its deterministic financing consequences.

**Capital Stack calculates financing consequences. It does not authorize financing.**

This phase establishes the calculation boundary for future lender intelligence, debt sizing, and Investment Committee analysis without adding lender execution or autonomous financing authority.

## 2. Sources

A `CapitalSource` represents a proposed source of capital, including senior debt, subordinate debt, mezzanine debt, preferred equity, common equity, or sponsor equity.

Each source has an explicit amount and provenance. Debt sources require `DebtTerms`.

Financing terms are not automatically facts. They may be `SOURCE` or `ASSUMPTION` depending on their origin.

## 3. Uses

A `CapitalUse` represents an explicit use of capital, such as:

- acquisition price
- acquisition costs
- financing costs
- reserves
- capital expenditures
- tenant improvements
- leasing commissions
- other approved uses

The foundational invariant is:

**TOTAL SOURCES = TOTAL USES**

The model exposes total sources, total uses, variance, and balanced status. An imbalance is not silently repaired.

## 4. Debt Terms

The initial deterministic debt model supports fixed-rate amortizing debt with:

- principal
- annual interest rate
- amortization period
- maturity
- annual debt service
- annual principal reduction
- balloon balance at maturity

Invalid debt terms are rejected.

## 5. Financing Calculations

Where sufficient inputs exist, the engine calculates:

- total debt
- equity requirement
- loan-to-value (LTV)
- loan-to-cost (LTC)
- annual debt service
- debt service coverage ratio (DSCR)
- debt yield
- leveraged property cash flows
- principal reduction
- balloon exposure

These outputs are explicitly classified as `CALCULATION`.

The engine does not calculate or replace the existing Pro Forma operating economics.

## 6. Provenance

The existing provenance vocabulary is preserved:

- `FACT`
- `SOURCE`
- `ASSUMPTION`
- `HYPOTHESIS`
- `CALCULATION`
- `INTERPRETATION`
- `PREDICTION`
- `RECOMMENDATION`

A proposed interest rate supplied by a lender dataset may be a `SOURCE`; a hypothetical rate used for analysis may be an `ASSUMPTION`. Debt service calculated from that rate is a `CALCULATION`.

Agent-supplied financing metrics such as DSCR, LTV, LTC, debt yield, or debt service cannot become authoritative calculation inputs.

## 7. Relationship to Pro Forma

The boundary is:

```text
PRO FORMA
    ↓
OPERATING ECONOMICS
    ↓
CAPITAL STACK
    ↓
FINANCING CONSEQUENCES
```

Capital Stack consumes authoritative Pro Forma operating cash flow and NOI. It does not recalculate NOI or mutate the Pro Forma result.

Unlevered economics remain separate from financing economics.

## 8. Relationship to Scenario Engine

Capital Stack does not create a second scenario engine and does not run financing Monte Carlo simulations.

The intended future relationship is:

```text
PRO FORMA
    ↓
CAPITAL STACK
    ↓
SCENARIO ASSUMPTION VARIATION
    ↓
FINANCING CONSEQUENCES
    ↓
SIMULATION
```

This allows future analysis of DSCR, debt yield, leverage, interest-rate exposure, and refinancing consequences under existing scenarios without duplicating scenario infrastructure.

## 9. Future Lender Intelligence Boundary

Future lender intelligence may provide proposed financing terms to the Capital Stack layer.

It must not contaminate the deterministic calculation layer.

```text
LENDER INTELLIGENCE
        ↓
PROPOSED FINANCING TERMS
        ↓
CAPITAL STACK
        ↓
DETERMINISTIC FINANCING ANALYSIS
        ↓
SCENARIOS / SIMULATION
        ↓
CONTRARIAN
        ↓
META-INTELLIGENCE
        ↓
HUMAN AUTHORIZATION
```

This phase does not scrape lenders, rank lenders, contact lenders, submit loan applications, or connect external lender APIs.

## 10. Human Authorization Boundary

Capital Stack cannot:

- approve financing
- authorize debt
- authorize equity
- approve a lender
- authorize capital structure
- create an investment authorization
- create a portfolio position
- deploy capital
- execute a transaction

A financing analysis may identify insufficient DSCR or excessive leverage. It does not turn that observation into a workflow decision.

The governing rule remains:

**AUTOMATION BETWEEN GATES. HUMAN AUTHORITY AT GATES.**

## 11. Limitations

This foundation intentionally does not model every financing structure. It does not currently provide:

- variable-rate debt
- interest-only periods
- complex amortization conventions
- lender-specific covenants
- prepayment penalties
- financing-market data
- lender matching
- automated lender outreach
- loan application execution
- autonomous refinancing
- financing Monte Carlo simulation

Those may be added only as distinct, auditable layers with explicit provenance and authority boundaries.
