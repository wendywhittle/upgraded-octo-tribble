# AletheiaTelos Institutional Learning Loop

AletheiaTelos treats forecasts as auditable research artifacts rather than ephemeral model output.

1. An agent may emit an explicit `predicted_probability`.
2. `AgentRunner` assigns a stable `prediction_id` derived from the agent, model version, question, and evidence context.
3. The forecast remains immutable.
4. A later outcome is attached through `/predictions/resolve` as a separate resolution record.
5. Brier error and calibration statistics are calculated from resolved forecasts.
6. `/observer/learning` projects agent-level performance and lessons.
7. Learning is informational only: authority, weights, execution permissions, brokerage access, and portfolio state are never changed automatically.

This preserves the distinction between **learning from history** and **changing the system's governing authority**.

CI verification: all changes to `main` must arrive through the protected pull-request workflow.
