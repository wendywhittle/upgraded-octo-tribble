# AletheiaTelos Architecture

## Product

AletheiaTelos is a real-estate deal flow engine.

DEAL INTAKE → DEAL RECORD → UNDERWRITING → EXCEL → PIPELINE

There are no agent swarms, event buses, provider forests, speculative research layers, or microservices in the first working version.

## Canonical Deal Record

One Deal Record is created for every accepted submission.

It contains:
- immutable Deal ID
- original submitted inputs
- derived values
- unavailable or missing values
- contact information
- status
- created / updated timestamps

Original inputs are never overwritten by calculations.

## Underwriting contract

The calculation layer is deterministic and independent of the web interface.

NOI:
1. Use explicit NOI when supplied.
2. Otherwise calculate EGI minus operating expenses when both exist.
3. Otherwise NOI is unavailable.

Core calculations:
- cap rate = NOI / purchase price
- loan amount = purchase price × LTV
- initial equity = purchase price - loan amount + closing costs
- annual debt service = mortgage payment × 12
- DSCR = NOI / annual debt service
- annual cash flow = NOI - annual debt service
- cash-on-cash = annual cash flow / initial equity
- exit value = NOI / exit cap rate
- IRR and equity multiple only when a sufficiently complete hold-period cash-flow model exists

Invalid or incomplete inputs do not become zeros.

## Excel

The workbook is generated from the canonical Deal Record.

Sheets:
1. Deal Summary
2. Operating Inputs
3. Financing
4. Returns
5. Missing Data

The application remains authoritative. The workbook is a portable analytical artifact.

## Persistence

The first implementation uses SQLite behind a small repository layer. The database path is configurable with ALETHEIA_DB_PATH.

For durable Render persistence, use a managed datastore or a paid persistent disk. The application does not pretend ephemeral storage is durable.

Schema changes are additive only: new tables are created with CREATE TABLE IF NOT EXISTS on startup (see app/schema.py). Existing tables and the deals in them are never altered, dropped, or rewritten.

## Evidence Log

Every material claim attached to a deal is recorded with an epistemic type, a source, and a timestamp (Charter §2.2, §13):

- observed: a directly observed fact
- sourced: information from a named source
- calculated: a computed value with a stated basis
- assumed: an assumption being carried forward
- hypothesis: an untested belief

Downstream analysis weighs evidence by type instead of treating all claims alike.

## Perspectives

Four deterministic analytical lenses examine each deal: Bull, Bear (contrarian), Quant, and Skeptic (Charter §3). These are not autonomous agents. Each lens is a fixed, documented methodology (see app/perspectives.py): a pure function of the deal's inputs, derived metrics, missing data, and evidence log.

Each lens records: belief, why, supporting evidence, contradicting evidence, key assumptions, uncertainty, and what would change its conclusion. Lenses are stored as separate append-only records and are never merged or averaged, so disagreement stays visible (Charter §2.1, §10).

## Scenarios

Base / bull / bear scenarios, plus custom named scenarios, vary NOI, exit cap rate, interest rate, and hold years, then run each through the existing underwrite() (Charter: scenario analysis). Default bull/bear shifts are documented scenario assumptions, not forecasts. Every scenario's definition is stored alongside its result so any number traces to the assumptions behind it.

## Risk Simulation

Monte Carlo over user-supplied input ranges (min/max per input), seeded for determinism: identical seed plus identical inputs always reproduce the identical summary (Charter: risk simulation). Reports p10/p50/p90 for IRR, equity multiple, and cash-on-cash, plus P(IRR < 0), P(cash-on-cash < 0), and the fraction of draws where IRR is uncomputable. Documented limitation: draws are independent uniform per input and ignore correlations, so joint-tail risk is understated.

## Uncertainty and Ranges

An input may be submitted as a [low, high] range. Wherever ranges appear, outputs are reported as [min, max] intervals evaluated over the corner combinations of the ranges, never as point estimates pretending the uncertainty away. A range is a bound on belief, not a calibrated distribution; distributions belong to simulation.

## Decision Journal and Observer

When a deal moves to PURSUE, the human may record a thesis: what they believe, the key assumptions it rests on, and the expected outcome. Later, an outcome (what actually happened) and a lesson can be recorded. Theses are immutable once recorded; an outcome never edits the thesis it follows (Charter §8, §20).

The Observer compares theses against outcomes side by side and lists lessons learned verbatim. It does not score or grade decisions. The journal records human decisions; it never makes them (Charter §5).

## API

Deal flow:

- GET / landing and intake interface
- GET /health
- POST /api/deals
- GET /api/deals
- GET /api/deals/{deal_id}
- PATCH /api/deals/{deal_id}/status
- GET /api/deals/{deal_id}/excel

Charter capabilities:

- POST /api/deals/{deal_id}/evidence — record an evidence item {type, source, content}
- GET /api/deals/{deal_id}/evidence — list evidence for a deal
- POST /api/deals/{deal_id}/perspectives — run lenses {lenses?}; stores each lens separately
- GET /api/deals/{deal_id}/perspectives — list stored perspective records (history preserved)
- POST /api/deals/{deal_id}/scenarios — run scenarios {scenarios?}; defaults to base/bull/bear
- GET /api/deals/{deal_id}/scenarios — list stored scenario runs with definitions
- POST /api/deals/{deal_id}/simulate — Monte Carlo {ranges, n?, seed?}
- GET /api/deals/{deal_id}/simulations — list stored simulation runs
- POST /api/deals/{deal_id}/thesis — record decision thesis (PURSUE deals only)
- GET /api/deals/{deal_id}/thesis — list recorded theses
- POST /api/deals/{deal_id}/outcome — record actual outcome and lesson
- GET /api/observer — theses vs outcomes side by side, lessons learned, counts

## Boundaries

The system may calculate, organize, compare, and expose information.

It does not:
- move capital
- execute trades
- place brokerage orders
- custody assets
- autonomously authorize an investment
- convert an analytical result into human authorization

The human remains the decision authority.

## Extension rule

New functionality must answer a concrete deal-flow need. A new abstraction, service, agent, provider, dashboard, or model does not enter the architecture merely because it is technically possible.

Build the workflow first. Add intelligence where it removes real friction.
