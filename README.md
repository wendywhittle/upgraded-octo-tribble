# AletheiaTelos

## Deal Flow Engine

AletheiaTelos is a working real-estate deal flow system.

DEAL INTAKE → CANONICAL DEAL RECORD → DETERMINISTIC UNDERWRITING → USEFUL RESULT → EXCEL MODEL → INTERNAL PIPELINE

The product starts with the opportunity, not a dashboard.

### What the user can do

1. Enter a property or deal.
2. Supply the numbers they actually know.
3. Submit the deal.
4. Receive a canonical Deal ID.
5. See calculations supported by the supplied information.
6. See what is missing instead of seeing invented assumptions.
7. Download an Excel model generated from the same Deal Record.
8. Review deals through a simple internal pipeline.

### Intake

Core: deal/property name, asset type, location, purchase price, annual NOI.

Optional: annual EGI, annual operating expenses, occupancy, LTV, interest rate, amortization period, hold period, exit cap rate, closing costs.

Contact: name, email, phone.

### Rules

- Explicit NOI wins.
- If NOI is absent and EGI plus operating expenses are supplied, NOI is derived.
- Missing values stay missing.
- No silent zeroes.
- No fabricated assumptions.
- Every calculated result identifies its basis.
- Repeated calculations with the same inputs are deterministic.

### Source of truth

The Deal Record is authoritative. Original inputs are preserved separately from derived values. Excel is an output artifact, not the source of truth.

### Pipeline

NEW → REVIEWING → PURSUE / HOLD / PASS

### Boundary

AletheiaTelos provides analysis and workflow support. It does not autonomously authorize investments, move capital, execute trades, or represent a human decision as system authority.

### Product rule

**If a screen does not help move a real deal forward, it does not belong in the first version.**

This repository favors a small working system over architectural ceremony.
