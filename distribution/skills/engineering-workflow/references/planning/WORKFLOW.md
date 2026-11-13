# Engineering workflow 0.1 — Planning

Status: project-local implementation; personal skill installation unavailable.

## Scope
Turn a software request into a reviewable execution plan. Support plan, resume,
and audit requests. Do not implement the proposed product change, publish
issues, install dependencies, or modify external systems merely to plan.
Read-only investigation is allowed. Run bounded isolated experiments only
within the user's authorization; label speculative conclusions explicitly.

## Procedure
1. Read project instructions, configuration, existing task records, and relevant
   source. On resume, compare source revision and artifact revisions with those
   last reviewed. Mark affected decisions, tasks, and reviews stale.
2. Write a brief: objective, observable acceptance criteria, exclusions,
   constraints, known facts, assumptions, and open questions. Ask only questions
   that block a meaningful decision; investigate discoverable facts yourself.
3. Select a route by uncertainty, coupling, impact, and reversibility. Small:
   local and clear; standard: understood feature boundary; complex: uncertain
   or cross-service; critical: money, authorization, or irreversible data.
   Explain the selection. Escalate when evidence changes it. Small tasks use
   one compact record; complex tasks use the full template.
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
9. Produce a dependency graph of tasks. Each has ID, objective, inputs and
   revisions, dependencies, scope, outputs, acceptance checks, capability
   profile, reviewer, and integration order. Assign one owner per shared
   contract/file set. Do not parallelize conflicting changes. Unresolved
   experiments block dependent implementation; conditional tasks are explicit.
10. Request independent plan review with the brief, evidence, specification,
    plan, and repository context, without the author's persuasive rationale.
    Review requirement coverage, feasibility, dependency cycles, verification,
    failure cases, scope, and integration. Reviewer must be a separate session
    when available. Otherwise label self-review and leave independent review
    outstanding for standard/complex/critical work.
11. Resolve findings and re-review affected sections. After two unsuccessful
    rounds, escalate with options or propose a bounded experiment. Never
    interpret the round limit as permission to ignore blockers.
12. Stop at planning completion. Report artifacts, route, decisions, remaining
    blockers, and next executable task. Do not begin implementation.

## Readiness
READY requires every acceptance criterion mapped to tasks and checks, no
unresolved blocking questions/findings, acyclic dependencies, and reviews of
current revisions. Standard/complex/critical routes require independent review.
Small routes may use an explicitly labeled self-review. Use BLOCKED for missing
product decisions, CONDITIONAL for unresolved experiments, and DRAFT otherwise.
A structural validator cannot establish semantic correctness or real review.

## Capability routing
Use fast models for bounded extraction, coding-capable models for repository
analysis and task decomposition, and deep reasoning for uncertain design and
critical audits. Record requested and actual capabilities. Host support governs
model selection; never fabricate model switches or independent reviews.

## Project adaptation and state
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
