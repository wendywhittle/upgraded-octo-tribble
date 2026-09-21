# AletheiaTelos Growth Engine Experiment

This is a bounded experiment for persistent prospect state. It is not part of the public deal-intake surface and is not deployed to Render by this branch.

## Purpose

Test the missing layer identified during the Astra-style workflow experiment:

DISCOVER -> RESEARCH -> QUALIFY -> CONTACT -> OUTREACH -> WAIT -> RESPOND -> FOLLOW-UP -> CONVERTED / STOPPED

The first implementation stores durable prospect state without granting the growth subsystem authority over investment decisions or external communications.

## State model

Each prospect records:

- prospect_id
- account
- people
- evidence
- qualification
- current_state
- next_action
- outreach_history
- response_history
- stop_reason
- timestamps

The original evidence and outreach history are append-only. Current state is explicit and deterministic.

## Safety boundary

This experiment does not send email, make calls, submit forms, or otherwise contact external parties. It produces state and a next action only.

The Growth Engine must never authorize an investment, move capital, execute a trade, change a deal decision, or represent human approval.

## Success criterion

Given the same prospect record and event sequence, the resulting state must be deterministic.

The next infrastructure step, only after this state model proves useful, is a queue/worker that wakes up and processes one eligible next action.
