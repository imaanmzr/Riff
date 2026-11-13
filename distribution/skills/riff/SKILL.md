---
name: riff
description: Plan, execute, review, route agents, and resume software engineering tasks using explicit decisions, specifications, evidence, and recovery checkpoints. Use for feature planning, reviewed-plan implementation, independent audits, or interrupted engineering work. Scale process to task risk.
---
# Engineering Workflow

Version 0.4.2. One skill coordinates four phases. Read only the needed phase.

## Resolve paths first
Treat the directory containing this SKILL.md as SKILL_ROOT and the user's target
repository as PROJECT_ROOT. Every `planning/`, `execution/`, `recovery/` or
`routing/` path in bundled instructions means SKILL_ROOT/references/<path>.
Run Python utilities by their absolute paths; pass project artifacts as absolute
paths. Do not change working directory to the skill and accidentally inspect it
as the target project. Never write task state or configuration inside this skill.

Read the target project's applicable instructions (AGENTS.md, CLAUDE.md, Cursor
rules, and existing conventions); obey the current host's instruction precedence. Optional project
settings live in PROJECT_ROOT/.engineering-workflow/project.json; routing.json
and host.json in that same directory supply routing settings. Task records belong
in PROJECT_ROOT/docs/work/<task-id>/ unless project settings override that path.

## Choose operation
- Plan: read references/planning/WORKFLOW.md. Stop after a reviewed plan.
- Execute: read references/planning/WORKFLOW.md and references/execution/WORKFLOW.md.
  Require user authorization to execute, not merely a READY plan.
- Audit: inspect the supplied spec/plan/code independently using the review rules
  in references/planning/WORKFLOW.md and references/execution/WORKFLOW.md.
- Resume/checkpoint: also read references/recovery/WORKFLOW.md.
- Delegate/select models: also read references/routing/WORKFLOW.md.

Preserve scope and prior authorization. If a planning request is ambiguous,
start with discovery and planning; do not silently begin product implementation.
Use brief records for small tasks and full templates only where useful.

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
