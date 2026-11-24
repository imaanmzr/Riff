---
name: riff
description: Research, design, debug, document, plan, execute, review, and resume engineering work. Scale investigation and verification to uncertainty and risk.
---
# Engineering Workflow

Version 0.8.0. Read references for the requested operation and current uncertainty.

## Resolve paths
The directory containing this file is SKILL_ROOT. The target repository is
PROJECT_ROOT. Bundled planning/, execution/, recovery/ and routing/ paths mean
SKILL_ROOT/references/<path>. Run utilities by absolute path and pass absolute
project artifact paths. On Windows use `py -3` or `python` for `python3` examples.
Inspect the target project, and save its state there.

Read applicable project instructions and obey host instruction precedence.
Optional settings live in PROJECT_ROOT/.engineering-workflow/project.json,
routing.json and host.json. Task records default to PROJECT_ROOT/docs/work/<id>/.
Use plan.md, plan.json and run.json so the CLI can find them.

## Select guidance
- Plan: read [Planning](references/planning/WORKFLOW.md), including its default
  clarification loop. Assess missing intent and important edge cases; ask focused
  questions before settling dependent decisions. For unclear behavior,
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
- Resume/checkpoint: also read [Recovery](references/recovery/WORKFLOW.md).
- Delegate/select models: also read [Routing](references/routing/WORKFLOW.md).

Load engineering guides selectively. Reuse current decisions and evidence by
path/ID. Summarize changes and open questions instead of copying full artifacts.
Use existing project terminology and record meaningful clarifications in its
current specification or glossary. Examples in guides support judgment.

## Gates and evidence
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
Unknown freshness cannot establish readiness. Read [Hosts](references/hosts.md)
for invocation, handoffs and verified capabilities. The host supplies model access.
Publication, deployment and installing external workflow packs require authority
within the user's request.
