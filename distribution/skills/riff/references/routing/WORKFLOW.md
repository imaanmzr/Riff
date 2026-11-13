# Routing 0.4

Read planning, execution and recovery instructions. Route only READY authorized
work. This utility proposes implementation assignments; coordinator invokes the
host's real tools and handles research/reviewer assignment under the same budgets.
Never interpret a proposal as a launched model or a resource reservation.

## Configure
Map fast/coding/deep_reasoning to actual supported host model identifiers in
config.json. Record current host availability and verified capabilities using
host.example.json. Empty mappings intentionally dispatch nothing. Do not assume
model names or capabilities from this example. Shared profile names use
underscores. Retain project-specific choices; do not silently replace budgets.
Task write_paths must be literal repo-relative file/directory prefixes. Unknown
scope takes exclusive ownership. Include shared contracts and generated files.

## Select
Run router.py --plan PLAN --run RUN --config CONFIG --host HOST.
The router honors execution gates, integrated dependencies, concurrency, active
reservations, path conflicts, attempt limits and available model mappings.
Critical work and prior failed attempts require deep_reasoning. No automatic
capability downgrade occurs. A failed attempt still requires explicit coordinator
resolution before the task becomes pending; routing does not reset blocked tasks.
No parallel agents or workspace isolation means one task at a time.

## Dispatch protocol
One coordinator owns selection and dispatch. While active agents exist, persist
run.tasks[T].routing with attempts and reserved_tokens, and the actual agent/model.
Record spent_tokens under run.routing. Account for review/research usage too.
Token counters must include all workflow model usage, not just coding.
Before launching, verify proposal snapshot is still current; reserve selected
budgets and mark tasks running in one generation-checked recovery checkpoint.
Then launch. If launch outcome is uncertain, keep the reservation and reconcile
through Recovery; never blindly redispatch. Persist actual host return values.
The proposal's proposed_model is not evidence of the model actually used.

available_slots is total capacity allocated to this workflow including its active
agents, not additional free capacity. Running/review records occupy a slot and
retain their token reservation. As usage is observed, transfer it from reserved
to spent without double counting. Retain a positive reservation while active;
stop dispatch on unavailable accounting instead of treating usage as zero.
On finish release unused reservation and record final actual usage. A provider
may exceed estimates: these are dispatch budgets, not guaranteed billing caps.
Enforce per-call limits in the host when supported. If counters are unavailable,
use conservative charged reservations and label them estimates; do not invent
precise usage or prices. Human budget changes must be explicit in task context.

## Review and escalation
Reviewers receive fresh context and raw artifacts, and must be separate sessions
from authors for non-small work. Different models are optional, independence is
required. Reserve reviewer capacity/budget before dispatching review. Model
unavailability leaves a review outstanding; it never waives completion gates.
After repeated failures, investigate the cause and replan rather than escalating
models indefinitely. Recovery drift blocks routing through execution gates.

## Evaluate
Compare the same representative tasks against sequential single-model execution.
Record accepted requirements, defects found after completion, rework, elapsed
time, actual/estimated tokens, selected/actual models, and human interventions.
Never claim better cost or quality without these measurements. No provider SDK,
model launcher, dynamic pricing, distributed scheduler or automatic spending
control is included in this release.
