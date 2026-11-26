# Engineering workflow 0.1 — Planning

The canonical planning instructions are bundled with the installed Riff skill.

## Scope
Turn a software request into a reviewable execution plan. Support plan, resume,
and audit requests. Do not implement the proposed product change, publish
issues, install dependencies, or modify external systems merely to plan.
Read-only investigation is allowed. Run bounded isolated experiments only
within the user's authorization; label speculative conclusions explicitly.

## Procedure
Consult relevant sections of the optional project guide using
[Onboarding's location and maintenance rules](ONBOARD.md#use-during-later-work).
Verify relevant claims; a missing guide does not require onboarding.

1. Read project instructions, configuration, existing task records, and relevant
   source. On resume, compare source revision and artifact revisions with those
   last reviewed. Mark affected decisions, tasks, and reviews stale.
2. Write a brief: objective, observable acceptance criteria, exclusions,
   constraints, known facts, assumptions, and open questions. Before settling the
   proposed behavior, use [Clarify intended behavior](#clarify-intended-behavior)
   to uncover material missing intent and important edge cases. Investigate
   discoverable facts yourself.
3. Use the [route rubric](#route-rubric) to select the effort for this task.
   Consult [Requirements & Design](DESIGN.md) for unclear behavior, overloaded
   terms, incomplete acceptance examples or consequential design choices. Use
   [Documentation](DOCUMENTATION.md) when a change needs durable docs.
4. Inspect existing behavior before proposing new architecture. Record evidence
   with source paths/revisions or external primary-source URLs and access dates.
   Distinguish observations, inferences, assumptions, and unresolved questions.
5. Commission bounded research only for material unknowns. Give each researcher
   a question, constraints, sources, expected output, and budget. Request
   alternatives, counterevidence, and recommendation. Parallelize independent
   questions. If delegation is unavailable, record sequential investigation.
6. Resolve important choices in decision records: alternatives, criteria,
   selection, evidence, consequences, owner, uncertainty, and reopening trigger.
   Use a concrete decision session, not simulated meeting dialogue. Resolve
   disagreement through evidence or an experiment, not majority vote. Ask the
   user only for unresolved product intent or consequential risk choices.
7. Specify behavior, contracts, invariants, failure paths, compatibility,
   migration/rollback, observability, and acceptance examples as relevant.
   Mark non-applicable sections with rationale. Do not invent repository paths.
8. Audit the specification against requirements and domain invariants. Every
   finding needs an ID, severity, evidence, consequence, and resolution test.
9. Plan the smallest end-to-end behavior each task can demonstrate. A small
   change normally needs one task entry with no dependencies. Each entry has
   ID, objective, inputs and revisions, dependencies, scope, outputs, acceptance
   checks, capability profile, reviewer, and integration order. Assign one owner
   per shared contract/file set. Do not parallelize conflicting changes. Unresolved
   experiments block dependent implementation; conditional tasks are explicit.
10. Use labeled self-review for small plans unless independent review is needed.
    For all other routes, request independent plan review with the brief,
    evidence, specification, plan, and repository context. Provide the artifacts
    without the author's persuasive rationale.
    Use [review technique](../execution/REVIEW.md) for coverage, feasibility,
    verification and failure cases; check dependency cycles, scope and integration.
    When the route requires independent
    review, use a separate session. If none is available, label any self-review
    and leave independent review outstanding.
11. Reassess the route before marking the plan READY. Resolve findings and
    re-review affected sections. After two unsuccessful rounds, escalate
    with options or propose a bounded experiment. Never
    interpret the round limit as permission to ignore blockers.
12. Stop at planning completion. Report artifacts, route, decisions, remaining
    blockers, and next executable task. Do not begin implementation.

For existing task records, preserve portable context in task-local `handoff.md`
after meaningful decisions and task transitions, following
[Recovery's portable context rules](../recovery/WORKFLOW.md#portable-task-context).
Read and preserve earlier context before updating; keep new requirements and
consequential decisions in the plan as well. Exclude handoffs and conversation
archives from automatically authored source inventories and review bindings,
while preserving explicit user entries.

## Clarify intended behavior

Assess every request after initial discovery, even when it sounds implementable.
Look for gaps in the user's outcome, scope, business rules and acceptance examples.
Walk through a successful use and the boundary or failure cases likely to change
the design. Consider permissions, empty/invalid inputs, repetition, interruption
or partial completion where relevant; do not turn these into a universal checklist.

Ask the user about remaining gaps that materially change behavior, scope, checks
or consequential risk. Use a few focused questions per round, normally one to
three related questions, then follow up if material gaps remain. Ground each in a
concrete scenario, explain why the answer matters, and offer meaningful choices
and a recommendation when useful. Allow the user to describe another outcome.
Do not merely list open questions in a finished plan or ask a vague "anything
else?". A clear request with no material gaps needs no manufactured questions.

Wait for answers before settling dependent decisions; independent read-only
investigation may continue. Reuse prior answers on resume/replan, reopening them
only when changed intent or evidence makes them stale. If the user skips questions,
disclose reasonable low-consequence assumptions. Keep unresolved material product
or risk choices explicit and blocking; silence or elapsed time is not an answer.

Record Q-* references, answers or explicit assumptions in the existing authored
plan and link them to R-* requirements and C-* acceptance examples, including the
important edge cases. Put still-blocking questions in plan.json's
unresolved_questions and name their owner and dependent work in the authored plan.
They prevent READY under the existing gate. Keep optional ideas explicitly
excluded/deferred with rationale outside that blocking list. For a small clear
change, keep this record brief rather than adding an interview transcript.

## Route rubric

After initial discovery, choose the highest route supported by the evidence.
Consider uncertainty, coupling, consequences of failure, and reversibility.
Assess the behavior affected by the change, regardless of the size of the diff.
Treat the route from `riff new` as provisional until discovery confirms it.

| Route | When it fits | Effort |
| --- | --- | --- |
| Small | Clear, local, reversible change within an existing contract, such as a copy fix | One compact plan and one task. Inspect the affected behavior, run a focused check and required project checks, and record labeled self-review. |
| Standard | Understood change to a feature contract, such as adding an optional API filter, even if the edit is local | Describe affected contracts and acceptance examples. Deliver in testable slices and obtain independent review. |
| Complex | Material uncertainty or tightly coupled changes | Use the full plan. Compare viable designs, resolve blocking unknowns, and verify interactions across affected boundaries. Run a bounded experiment when it can settle a decision and is authorized. |
| Critical | Failure could cause serious harm, such as duplicate charges, unauthorized access, or irreversible data loss | Specify invariants, failure modes, and recovery. Verify those paths and obtain independent plan and execution reviews, including an invariant audit. |

Record the route and a brief rationale in `plan.md` and the same route in
`plan.json`. For a standalone design, architecture audit, or docs request,
state the route and rationale in the response and consult the existing task
record if supplied. Preserve read-only scope when the user asks for advice
or an audit.

For small plans, keep the Markdown brief and fill the existing machine record.
Include the expected result, evidence, verification, and labeled self-review.
Add detailed sections only where the task calls for them. If new evidence
changes the route, explain what changed and re-review the affected plan.

## Readiness
READY requires every acceptance criterion mapped to tasks and checks, no
unresolved blocking questions/findings, acyclic dependencies, an actual source
baseline (revision or content fingerprints), and reviews of current revisions.
Standard/complex/critical routes require independent review.
Small routes may use an explicitly labeled self-review. Use BLOCKED when a
missing decision or external fact prevents a safe plan, CONDITIONAL when a
bounded experiment can resolve the remaining uncertainty, and DRAFT otherwise.
In `plan.json`, bind each qualifying review to the plan's `revision` and
`source_revision`. Use the structural validator to check the record.
A structural validator cannot establish semantic correctness or real review.

## Capability routing
Use fast models for bounded extraction, coding-capable models for repository
analysis and task decomposition, and deep reasoning for uncertain design and
critical audits. Record requested and actual capabilities. Host support governs
model selection; never fabricate model switches or independent reviews.

## Project adaptation and state
For v2 records and live review binding, read [Record contracts](RECORDS.md).
Use [Research](RESEARCH.md), [Debug](DEBUG.md), and [Replan](REPLAN.md) for those
operations. Research/debug reports do not independently authorize implementation.
Write human-readable plans using the layered template: outcome and next action
first, then behavior/diagrams, decisions, delivery and detailed evidence. Keep
small plans compact. Diagrams supplement acceptance criteria, never replace them.
Read engineering guides only for the operation or an unresolved concern. Reuse
current decisions/evidence by reference and summarize changes and open questions.
Resolve the effective profile for the task. Use its `sections` as authoring
emphasis and map its `required_checks` to tracked verification. The route and
review requirements still follow the risk rubric and target project instructions.

Read `project.json` when supplied; missing settings remain unknown until
inspected. Use existing repository conventions and merge instructions rather
than replacing them. Store task records in the configured directory. Use
`templates/plan.md` and `templates/project.json` as starting points. Keep stable
requirement, decision, task, and finding IDs. Record workflow version, source
revision (or content hashes outside Git), artifact revision, stage, and next
step. Preserve earlier decisions as superseded rather than silently deleting.

## Invocation examples
- Plan partial refunds; stop after independent plan review.
- Resume plan REFUND-01 and check for stale assumptions.
- Audit this plan without changing product code.

## Validation
Run `python3 planning/tests/test_validate.py` for structural gate regression
checks. Run `python3 planning/validate.py path/to/plan.json` to check a machine
record. Use `tests/scenarios.md` for behavioral evaluations. Passing structural
checks is only one input to readiness.
