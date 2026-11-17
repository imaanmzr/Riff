# Routing 0.4

Ask: "Route the ready tasks using routing/WORKFLOW.md."

Configure profiles with real host model IDs and capabilities. Defaults have no
models, so they cannot accidentally pretend a model is available. Budget values
are editable initial defaults, not recommended spending or provider limits.

    python3 routing/router.py --plan plan.json --run run.json --config routing/config.json --host host.json

Per-task additions: capability (fast/coding/deep_reasoning), write_paths (literal
relative paths), optional token_budget. Running task records must contain
routing.reserved_tokens; record routing.attempts for attempts already launched.
Run-level routing.spent_tokens tracks charged/observed usage. The coordinator
must maintain accounting and checkpoint reservations before launching anything.
Review/research scheduling remains coordinator-managed under the same budget;
the router's output is for pending implementation tasks only.

Version 0.4 adds deterministic model selection with upward fallback, critical and
retry escalation, dependency gating, conflict-aware concurrency, budget and
attempt limits, plus a snapshot hash for detecting stale proposals. This is a
proposal tool, not a provider integration or multi-coordinator scheduler.

Validation: 50 regressions across all phases; routing contributes 18. A CLI test
checks two independent assignments and an exhausted-budget result. Performance,
cost and quality improvements are not yet measured. Use evaluation-template.json
for matched baseline/routed trials on real features before making those claims.

Existing planning-only and recovery behavior remains unchanged. All four phases
are project-local; personal skill installation remains outside this release.
