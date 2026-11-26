# Execution

The execution workflow implements an authorized, reviewed plan and records
verification and integration evidence. Read [WORKFLOW.md](WORKFLOW.md) for entry
requirements and task transitions.

## Use

Ask your agent to execute a saved plan:

```text
$riff Execute the reviewed plan at docs/riff/retry-fix/.
```

Use `/riff` in Cursor, VS Code Copilot, or Claude Code. Execution requires a READY
plan, user authorization, a matching source baseline, and current review evidence.
For behavior changes, follow the [implementation guide](IMPLEMENTATION.md).
Use the [review guide](REVIEW.md) for specification and code-quality reviews.

## Execution records

Use [template.json](template.json) to create `run.json` alongside the plan. Each
task records its state, assigned agent, candidate and integration revisions,
checks, reviews, and blockers. Checks identify their command, exit code, evidence,
and source revision. Reviews identify their kind, reviewer, independence,
verdict, evidence, and reviewed revision.

A task becomes eligible when its dependencies are integrated. The coordinator
must still check file conflicts, host capabilities, and concurrency limits.
`gates.py` evaluates the declared records; the host and coordinator run agents,
commands, and reviews.

## Validation

From the repository root:

```bash
python3 execution/gates.py path/to/plan.json path/to/run.json
python3 planning/tests/test_validate.py
python3 execution/tests/test_gates.py
```

The gate rejects missing authorization, unmet dependencies, stale verification,
and insufficient review evidence. It does not authenticate that evidence or run
the recorded checks. There is no background execution daemon or automatic retry
engine.
