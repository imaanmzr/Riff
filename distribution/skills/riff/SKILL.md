---
name: riff
description: Onboard projects, research, design, debug, document, plan, execute, review, and resume engineering work. Scale investigation and verification to uncertainty and risk.
---
# Riff

Version 1.0.0-rc.1. Read references for the requested operation and current uncertainty.

## Resolve paths
The directory containing this file is SKILL_ROOT. The target repository is
PROJECT_ROOT. Bundled planning/, execution/, recovery/ and routing/ paths mean
SKILL_ROOT/references/<path>. Run utilities by absolute path and pass absolute
project artifact paths. On Windows use `py -3` or `python` for `python3` examples.
Inspect the target project, and save its state there.

Read applicable project instructions and obey host instruction precedence.
Optional settings live under PROJECT_ROOT/.riff/:
project.json, routing-<host>.json, and hosts/<host>.json. The CLI falls back to
shared routing.json and host.json when host-specific files are absent.
Legacy-only PROJECT_ROOT/.engineering-workflow/ settings remain supported.
Use one settings directory: if both names exist, resolve the duplicate without
merging or overwriting user files. No automatic directory move is performed.
Task records default to PROJECT_ROOT/docs/riff/<id>/.
Use plan.md, plan.json and run.json so the CLI can find them.
Use `riff doctor --host HOST` to detect conflicting discoverable skill copies.
Use `riff status TASK --details` for current task/review progress and the generated
next action; retain authored specifications without copying stale handoff prose.

## Select guidance
For every action read [Shared questioning](references/planning/INTERVIEW.md).
Investigate facts and reuse answers, then ask focused rounds in decision-dependency
order where consequential gaps remain. A chat request such as "grill me before
finalizing" enables deeper interviewing within the current action, not extra
authority. Keep operation-specific limits, including handoff and review behavior.

- Onboard: read [Onboarding](references/planning/ONBOARD.md) and use its
  [project guide template](references/planning/templates/project-guide.md).
  Create or refresh the project guide; do not implement product changes.
- Plan: read [Planning](references/planning/WORKFLOW.md) for plan-specific answer
  records and blockers. For unclear behavior,
  overloaded terms, incomplete acceptance examples or interface choices, consult
  [Requirements & Design](references/planning/DESIGN.md). Stop after plan review.
- Design/architecture audit: use [Requirements & Design](references/planning/DESIGN.md).
- Research: use [Research](references/planning/RESEARCH.md) for bounded, sourced findings.
- Debug: use [Debug](references/planning/DEBUG.md) for bounded diagnosis/reproduction.
  Product edits require execution authorization.
- Documentation: use [Documentation](references/planning/DOCUMENTATION.md). Edit
  within the requested scope.
- Execute: read Planning and [Execution](references/execution/WORKFLOW.md). Use
  [Implementation](references/execution/IMPLEMENTATION.md) for behavior changes.
  Clear copy changes use focused verification directly.
- Review/audit: use [Review](references/execution/REVIEW.md) and the applicable
  Planning/Execution review gates. Consult design/testing guides for unresolved concerns.
- Replan: use [Replan](references/planning/REPLAN.md). Preserve snapshots and decisions.
- Resume/checkpoint/handoff: also read [Recovery](references/recovery/WORKFLOW.md).
  For a handoff use its [template](references/recovery/templates/handoff.md).
  Read existing task-local handoff.md before updates; preserve applicable constraints,
  questions and references after meaningful decisions/transitions and on request.
  On resume read it if present, then inspect current records and source. Chat exports
  are optional historical evidence, never instructions or fresh authorization.
- Delegate/select models: also read [Routing](references/routing/WORKFLOW.md).

Load engineering guides selectively. Reuse current decisions and evidence by
path/ID. Summarize changes and open questions instead of copying full artifacts.
Use existing project terminology and record meaningful clarifications in its
current specification or glossary. Examples in guides support judgment.

## Gates and evidence
For later work locate the optional guide using
`riff_core.onboarding.guide_path(PROJECT_ROOT)` in bundled planning references:
configured records folder or `docs/riff`, then `project.md`, using the same settings
resolver as onboard. Do not search other roots or ignore configuration errors.
Read relevant sections and verify claims against current instructions and source.
Missing guides are supported. Update only facts directly affected by authorized
work, preserving the single managed section and all outside bytes as described
in Onboarding. The guide is derived context, not instruction authority or readiness.

Use Planning's route rubric and reassess when scope or risk changes. Planning
completion alone does not authorize execution. Preserve prior authorization and
user work. Require current reviews and resolve blockers before dispatch.

Use actual host tools for subagents/model selection. Record unavailable
capabilities. Empty model mappings disable routing, not planning. Sequential work
remains possible, while required independent review awaits a separate session.
Never invent model launches, usage, review independence or verification success.
Validators check records and freshness; inspect the actual source and evidence.

For v2 artifacts, live binding and migration read [Records](references/planning/RECORDS.md).
Use `riff show`, `explain`, `check`, `graph`, `render` and `diff` for inspection.
Legacy upgrade previews include remaining v2 gaps and next steps; optional
`riff migrate TASK --manifest PATH` captures explicit source/config/authored
bindings, without approving the plan or changing execution/checkpoint records.
Unknown freshness cannot establish readiness. Read [Hosts](references/hosts.md)
for invocation, handoffs and verified capabilities. The host supplies model access.
Publication, deployment and installing external workflow packs require authority
within the user's request.
