---
name: riff
description: Design, document, plan, execute, review, and resume software engineering work. Use for interface design, architecture audits, project documentation, reviewed implementation, and recovery. Scale effort to task risk.
---
# Engineering Workflow

Version 0.8.0. Read the references relevant to the requested operation.

## Resolve paths first
Treat the directory containing this SKILL.md as SKILL_ROOT and the user's target
repository as PROJECT_ROOT. Every `planning/`, `execution/`, `recovery/` or
`routing/` path in bundled instructions means SKILL_ROOT/references/<path>.
Run Python utilities by their absolute paths; pass project artifacts as absolute
paths. On Windows, use `py -3` or `python` for examples that use `python3`.
Do not change working directory to the skill and accidentally inspect it
as the target project. Never write task state or configuration inside this skill.

Read the target project's applicable instructions (AGENTS.md, CLAUDE.md, Cursor
rules, and existing conventions); obey the current host's instruction precedence. Optional project
settings live in PROJECT_ROOT/.engineering-workflow/project.json; routing.json
and host.json in that same directory supply routing settings. Task records belong
in PROJECT_ROOT/docs/work/<task-id>/ unless project settings override that path.

## Choose operation
- Research: read [Research](references/planning/RESEARCH.md). Produce bounded,
  sourced investigation reports; distinguish facts, inference and uncertainty.
- Debug: read [Debug](references/planning/DEBUG.md). Diagnose and reproduce with
  bounded isolated diagnostics; do not edit product code merely to diagnose.
- Replan: read [Replan](references/planning/REPLAN.md). Preserve snapshots and
  superseded decisions, invalidate stale reviews, and stop before execution.
- Plan: read [Planning](references/planning/WORKFLOW.md). Stop after a reviewed plan.
- Design or audit architecture: use [Design & Architecture](references/planning/DESIGN.md).
  Analyze and recommend within the requested scope.
- Advise on or update project docs: use [Documentation](references/planning/DOCUMENTATION.md).
  Edit only when the request authorizes the documentation change.
- Execute: read [Planning](references/planning/WORKFLOW.md) and
  [Execution](references/execution/WORKFLOW.md), including its implementation guide.
  Require user authorization to execute, not merely a READY plan.
- Audit a spec, plan, or code change: inspect it independently using the review rules
  in references/planning/WORKFLOW.md and references/execution/WORKFLOW.md.
- Resume/checkpoint: also read references/recovery/WORKFLOW.md.
- Delegate/select models: also read references/routing/WORKFLOW.md.

Preserve scope and prior authorization. If a planning request is ambiguous,
start with discovery and planning; do not silently begin product implementation.
Use the [route rubric](references/planning/WORKFLOW.md#route-rubric) to match
effort to the task and reassess when material evidence changes.

## Host capabilities
Use real tools for subagents and model selection when available. Explicitly
record unavailable capabilities; never simulate independent review or claim a
model was launched from a routing proposal. Empty model mappings disable the
router, not planning. A capable current agent can work sequentially, but required
independent review remains outstanding until another session performs it.

## Evidence
Use bundled validators as structural checks, not proof of correctness. Read the
actual source, run relevant checks, preserve findings, and bind reviews to exact
revisions. Stop at unresolved blockers. Do not install other skill packs or
publish/deploy merely because this skill is invoked.

## Different hosts and models
Read references/hosts.md for invocation, model selection, and cross-host handoffs.
The workflow is model-independent; its tools do not invoke provider APIs. Use
only the active host's verified capabilities. A subscription or model visible
in another app does not establish access in the current host.

Use plan.json and plan.md for planning records and run.json for execution records
in each task directory so riff status, validate and route can locate them.
For v2 shapes, live binding and migration, read [Records](references/planning/RECORDS.md).
Use `riff show`, `explain`, `check`, `graph`, `render`, and `diff` to inspect work.
Explain recorded versus evaluated status; unknown freshness is not a pass.
