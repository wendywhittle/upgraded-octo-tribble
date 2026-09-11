# Phase 9 Visual Integration

The visual integration exposes the existing Phase 9 Investment Case Assembly through a read-only browser boundary.

`POST /phase9/visual` adapts CRE inputs into `assemble_investment_case()` and returns the existing Pro Forma, Scenario, CRE Simulation, Contrarian, Capital Stack, Lender Evidence, Investment Synthesis, and assembly outputs.

The browser performs no underwriting, IRR, DSCR, LTV, scenario, or simulation calculations. No lender evidence is invented; the visual boundary reports `UNKNOWN / NOT PROVIDED` when none is supplied.

The response explicitly reports that human authorization is required and that no authorization, workflow mutation, portfolio creation, lender selection, or transaction execution occurred.

This is an integration/observability surface, not an authorization surface and not a new analytical engine.
