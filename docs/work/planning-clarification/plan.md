# Focused clarification during Riff planning

## At a glance
Outcome: a Riff plan asks the user about material missing intent and important
edge cases before settling the proposed behavior.
Current status and review bindings: see plan.json. Route: standard because this changes
the planning interaction across CLI and skill entry points.
Baseline: eee5f1e5492e4b74dead818da3972a75671994cd; working tree initially clean.
Scope: planning guidance, generated planning prompts, the existing plan template,
user documentation, distribution parity and focused verification.
Initial next action: review this contract, then implement T-1 under the user's request
to add the feature. No deployment or installation into existing projects.

## Problem and proposed behavior
Observed: planning/WORKFLOW.md step 2 limits questions to those blocking a
meaningful decision. planning/DESIGN.md discusses boundaries, but is selectively
loaded. distribution/commands.py emits no explicit clarification instruction.
The user reports that planning skips critical questions and important edge cases.

The user selected a few focused questions at a time, including important edge
cases, continuing once material gaps are resolved. Every plan will assess missing
intent after initial discovery. Ask about the gaps that change outcomes, scope,
business rules, acceptance checks or consequential failure behavior. Investigate
repository facts first and reuse prior answers. Clear, complete requests need no
artificial question quota.

Example: "add partial refunds" should elicit the policy for refund limits and
repeated requests when those policies are unspecified, using concrete scenarios
and useful choices. It should not ask the user where existing refund code lives.
The answer becomes a requirement and success/boundary acceptance examples.

## Decisions and trade-offs
D-1: make the assessment part of the default planning workflow. An optional guide
alone is too easy to miss; a mandatory interview on every task adds friction.
D-2: use focused rounds, normally one to three related questions, with consequences
and a recommended option when useful. This is a default, not an arbitrary limit
that discards remaining material questions. Wait for the answer before resolving
dependent intent; independent read-only investigation may continue.
D-3: reuse existing authored plan sections and unresolved_questions. Record stable
Q-* references, answers/assumptions, and links to requirements/checks in plan.md.
Keep unresolved blocking questions in plan.json. No schema migration, new CLI
command, runtime interview engine or readiness-validator change is needed.
D-4: preserve planning-only scope and existing readiness/review rules. Explicitly
deferred nonblocking ideas can be excluded with rationale. A request to skip
questions permits disclosed safe assumptions, not invented answers to material
product or risk decisions. An unanswered material question prevents READY.

## Delivery and acceptance
T-1, owned by the root agent, has no dependencies. Inputs are this plan, the
recorded source baseline and the user's selected interaction. Scope includes
planning/{WORKFLOW.md,DESIGN.md,templates/plan.md,tests/scenarios.md},
distribution/{commands.py,skills/riff/SKILL.md,tests/test_cli.py}, the bundled
planning mirrors, README.md and docs/features.md. Output: default clarification
guidance reaches direct skill use, free-text planning, saved-task planning and
the legacy prompt alias, with consistent documentation and packaging.

R-1 / C-1: every planning entry point directs an intent/edge-case assessment and
focused questions before finalizing a plan; ordinary repository facts are inspected.
R-2 / C-2: answers become requirements and acceptance examples; unanswered material
questions remain blockers; clear requests and previously answered questions do
not cause redundant interviews; skipping questions cannot fabricate an answer.
R-3 / C-3: free-text/saved-task/legacy prompts preserve host invocation, project
location, effective profile and read-only prompt generation. Compare equivalent
entry points and verify task record bytes remain unchanged.
R-4 / C-4: canonical/bundled instructions match, fresh installations include the
guidance, and planning, execution and distribution suites pass. Exercise focused
behavioral scenarios separately from structural and prompt-wiring checks.

Required checks: Python unittest discovery in planning/tests, execution/tests and
distribution/tests; tools/sync_references.py --check; skill quick_validate.py;
independent specification, quality and final integration review. Recovery/routing
regressions apply if those contracts change; none are proposed here.

## Technical contract
The CLI continues to print prompts; the host agent conducts the conversation.
No external API, persistent schema or executable readiness gate changes. Existing
records remain valid. On resume/replan reuse answers and reopen only those made
stale by changed intent or evidence. Existing review invalidation still applies.
Rollback is reverting the guidance/prompt changes and resynchronizing references.
Observability is the recorded questions, answers, assumptions and acceptance checks.

## Evidence, questions and traceability
E-1: inspected planning/WORKFLOW.md, planning/DESIGN.md,
planning/templates/plan.md, distribution/commands.py and the packaged SKILL.md at
the baseline above. E-2: user requested focused question rounds in this chat.
No unresolved product decision remains for this slice. Actual review and
verification status belongs in plan.json, run.json and their linked evidence.

## Findings and review
Actual independent verdicts, candidate fingerprints and check results are
recorded in review.json and verification.json as each stage completes.

## Handoff
Implement T-1 only after a current qualifying plan review. Retain this plan's
source baseline; record candidate and integration evidence separately.
