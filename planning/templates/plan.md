# Planning record

## At a glance
Outcome: describe the observable improvement in one sentence.
Status: DRAFT. Route and rationale: assess after discovery.
Scope: what changes, and what is excluded.
Major uncertainty: record what still needs evidence.
Next action: name the next concrete decision or check.

## Problem and proposed behavior
Describe what happens today and what should happen instead. Include one concrete
before/after example. Separate inspected behavior from the proposed design.

## Clarification and edge cases
Record material Q-* questions actually asked, their answers or explicit assumptions,
and the R-* requirements/C-* acceptance examples they inform. Include the important
boundary and failure outcomes. For unanswered material questions, name the owner
and dependent decisions/tasks; keep them in plan.json's unresolved_questions and
do not mark READY. Put optional deferred ideas with scope exclusions instead.
Reuse earlier answers. If no material gaps remain, a brief statement is enough;
omit the interview detail for a clear small change.

## Visual explanation
Use a flow, sequence, component, or state diagram only when it clarifies this
change. Label it current/proposed/illustrative, give its source/revision and a
short textual explanation. Include relevant failure paths. Task dependencies are
generated from JSON; they are not runtime interactions. Omit this section for a
small change if prose is clearer.

## Decisions and trade-offs
Use D-* IDs matching JSON. Explain alternatives, criteria, selected behavior,
evidence, consequences, owner and the condition that would reopen the decision.
Preserve superseded decisions and link their replacements.

## Delivery and acceptance
Use R-* requirement, C-* acceptance-check and T-* task IDs matching JSON. Each task
states its demonstrable outcome, inputs/revisions, scope, owner/capability,
dependencies, outputs, acceptance checks, reviewer and integration order.
Generated task summaries and graphs appear in exported views.

## Technical contract
Specify behavior, interfaces, invariants, error/failure paths, compatibility,
migration/rollback, recovery and observability. Mark inapplicable items with a
reason. Link detailed specifications and add them to reviewed_artifacts.

## Evidence, questions and traceability
List source paths/revisions or primary URLs/access dates. Label observed,
inferred, assumed and unresolved statements. Give unresolved questions an owner.
Map requirement -> decision -> task -> acceptance check -> evidence.

## Findings and review
Use F-* finding IDs with severity, evidence, consequence and resolution check.
Record actual reviewer session, independent/self status, verdict, plan revision,
source revision and live authored/config/plan digests. Structural checks do not
prove evidence or reviewer independence.

## Handoff
State remaining uncertainty, blockers, conditional work and next task.
Planning completion alone does not authorize execution.
