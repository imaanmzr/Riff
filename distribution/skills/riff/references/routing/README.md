# Routing

Routing proposes model assignments for eligible implementation tasks. It uses
configured capabilities, task dependencies, file conflicts, concurrency limits,
token reservations, and dispatch attempt limits. Read [WORKFLOW.md](WORKFLOW.md)
for the dispatch protocol and accounting rules.

## Configure

Set model IDs and capabilities to values available in your current agent host.
Default mappings are empty. Budget defaults are editable planning values; they
are not provider billing limits or recommended spending.

Use `riff configure --host HOST` to save host-specific mappings. From the target
project, request a proposal for a saved task:

```bash
riff route retry-fix --host codex
```

For direct use from the Riff repository:

```bash
python3 routing/router.py --plan path/to/plan.json --run path/to/run.json --config path/to/routing.json --host path/to/host.json
```

## Records and dispatch

Tasks declare a capability profile (`fast`, `coding`, or `deep_reasoning`),
project-relative `write_paths`, and an optional token budget. The execution
record tracks reserved tokens and dispatch attempts per task, plus observed
usage for the run. The coordinator must persist reservations before launching
work and update accounting from host-reported usage.

The router proposes assignments for pending implementation tasks. Research and
review scheduling remains the coordinator's responsibility under the same
budget. Routing does not call provider APIs, launch agents, or maintain a shared
scheduler. The [adapter contract](ADAPTERS.md) includes a simulated adapter for
contract tests; no live provider adapter is shipped.

## Validation and evaluation

From the repository root:

```bash
python3 routing/tests/test_router.py
python3 routing/tests/test_adapters.py
```

Tests cover dependency gating, capability selection, file conflicts, budget
exhaustion, stale proposals, and simulated results. Use
[evaluation-template.json](evaluation-template.json) to record matched trials
before making claims about performance, cost, or quality improvements.
