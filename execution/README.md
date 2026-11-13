# Execution 0.2

Use: "Execute the reviewed plan using execution/WORKFLOW.md."
The repository AGENTS.md routes explicit implementation requests here.

Planning 0.1 remains supported. Execution requires a READY plan, actual user
authorization, matching baseline, and current review evidence. Fill template.json
with one task record per planned task. Run:

    python3 execution/gates.py plan.json execution.json
    python3 planning/tests/test_validate.py
    python3 execution/tests/test_gates.py

Task record fields: state, agent, candidate_revision, integration_revision,
checks, reviews, blockers; blocked tasks also need reason. Each check records
revision, command, exit_code, evidence. Each review records kind (spec, quality,
invariants or integration), revision, reviewer, independent, verdict, evidence.
Final verification uses the execution head_revision and includes requirements.

Eligible tasks are dependency-ready, not necessarily safe to run in parallel.
The coordinator must check scope conflicts and concurrency limits before dispatch.
The tool checks declared evidence, not its authenticity or semantic adequacy.
It does not spawn agents, mutate state, run shell commands, or enforce permissions.
No background daemon or crash-safe execution engine is included.

Validation: 8 planning regression tests and 12 execution regression tests.
Coverage includes failed checks, stale candidate/final evidence, self-approval,
unmet dependencies, missing authorization, and critical invariant review.
Real multi-worktree feature execution remains a pilot, not a completed benchmark.

Installation: project-local workflow only. Personal skill installation from 0.1
remains unresolved. This release does not claim global skill availability.
