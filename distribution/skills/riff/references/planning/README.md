# Planning

The planning workflow turns a software request into a reviewed specification and
task plan. Read [WORKFLOW.md](WORKFLOW.md) for the procedure, risk routes, and
readiness requirements. Planning stops before implementation.

## Use

With the Riff skill installed, ask your agent:

```text
$riff Plan the retry fix. Stop after plan review.
```

Use `/riff` in Cursor, VS Code Copilot, or Claude Code. When working directly in
this repository, the root `AGENTS.md` points to the same workflow.

## Records and guides

Store the human-readable plan in `plan.md` and structured data in `plan.json`.
Use the [templates](templates/plan.md) as starting points and replace example
values with evidence from the target project. New CLI tasks use schema v2;
[Record contracts](RECORDS.md) explains fields and review bindings.

Choose supporting guides for the work at hand:

- [Requirements and design](DESIGN.md): clarify behavior and compare approaches.
- [Research](RESEARCH.md): investigate a question and record sources and uncertainty.
- [Debugging](DEBUG.md): reproduce a problem and test diagnostic hypotheses.
- [Documentation](DOCUMENTATION.md): verify and update reader-facing instructions.
- [Replanning](REPLAN.md): revise a plan while preserving decisions and history.

A Small-route plan permits labeled self-review. Standard, Complex, and Critical
plans require independent review before they are ready. Record only reviews
that actually took place.

## Validation

From the repository root:

```bash
python3 planning/validate.py path/to/plan.json
python3 planning/tests/test_validate.py
python3 planning/tests/test_records.py
python3 planning/tests/test_reports.py
python3 planning/tests/test_presentation.py
```

Validation checks structure and, for v2 READY plans, current review bindings.
It cannot establish the truth of recorded evidence. The
[behavioral scenarios](tests/scenarios.md) provide additional evaluation cases.
