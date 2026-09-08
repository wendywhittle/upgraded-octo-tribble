# Registered Perspective Orchestration

AletheiaTelos now routes its simulation endpoint through the formal agent registry. The Computational Kaleidoscope roster is configuration-driven and contains the current research perspectives: Researcher, Quant, Investor, Scientist, Systems, Contrarian, Philosopher, Observer, Meta-Intelligence, and Governance/CHARTER.

The current deterministic implementations are scaffolding for the contract. They deliberately do not manufacture decision-usable evidence. When no verified evidence has entered the system, perspectives return `NO_DATA` and zero confidence.

This is intentional: the system must not preserve convincing demo claims by disguising synthetic assumptions as evidence.

The next provider can implement the same `Agent.assess(question, evidence)` contract using a model or other reasoning engine. Downstream conflict analysis, Monte Carlo simulation, Skeptic review, synthesis, Observer, memory, and governance remain outside the agent's authority.
