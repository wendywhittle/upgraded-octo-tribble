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

## API

- GET / landing and intake interface
- GET /health
- POST /api/deals
- GET /api/deals
- GET /api/deals/{deal_id}
- PATCH /api/deals/{deal_id}/status
- GET /api/deals/{deal_id}/excel

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

## User Data and Privacy Boundary

The public application accepts information submitted directly by users through the deal-intake interface. User-submitted information is governed by the dedicated USER_DATA_AND_PRIVACY_BOUNDARY.md document.

The core principle is:

**USER SUBMISSION ≠ AUTHORIZATION**

Submission of information does not authorize an investment, transaction, external action, movement of capital, brokerage activity, custody, representation of the user, or action over the user's assets or affairs.

The data-processing chain remains separate from consequential decision authority:

USER SUBMISSION → DATA PROCESSING → ANALYSIS

ANALYSIS → RECOMMENDATION → AUTHORIZATION → EXECUTION

The application should minimize unnecessary collection, distinguish user-submitted information from system-generated and derived information, preserve uncertainty, and apply appropriate security, retention, privacy, and third-party-processing controls. This boundary establishes architectural requirements and does not represent legal compliance certification or imply that every control is currently implemented.

See USER_DATA_AND_PRIVACY_BOUNDARY.md for the full boundary.
