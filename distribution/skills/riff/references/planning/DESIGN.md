# Requirements, design and architecture

Consult the relevant section when behavior or acceptance examples are unclear,
terms have conflicting meanings, or an interface/design choice affects the work.
Architecture audits use the final section. Scale effort with the
[route rubric](WORKFLOW.md#route-rubric). Standalone design/audit requests are
read-only by default. A clear local change can use its existing contract directly.

## Understand the requested behavior

1. Follow one concrete input through the existing caller and observable result.
   Inspect relevant tests and project terminology. Distinguish inspected behavior
   from the user's intended change.
2. Investigate repository facts first. Ask focused questions about remaining
   product intent that changes behavior or checks, using the planning workflow's
   [clarification loop](WORKFLOW.md#clarify-intended-behavior). Give concrete
   consequences for plausible interpretations and recommend an option when the
   evidence supports it. Reuse recorded answers rather than restarting discovery.
3. Work through a successful example and the failure or boundary case most likely
   to change the design. For numbers, include units and boundary values. For
   asynchronous work, consider repetition, interruption and partial completion
   when relevant. Ask which outcome is intended when an unspecified boundary
   would require choosing a user-visible policy. Resolve material uncertainty.
4. Turn the examples into observable requirements and checks in the existing plan.
   Record assumptions explicitly. Use the project's established terms. Resolve
   confusing terms in its current glossary or specification; create durable docs
   only when the convention or decision warrants them.

Example: "show active customers" could mean a recent login or a current paid
subscription. Inspect the existing filter and ask which meaning applies. If the
answer is "paid subscription at the requested time", specify expired and future
subscriptions as acceptance examples. Keep that meaning beside the requirement.

Avoid asking users to locate discoverable code or designing storage before
behavior is settled. Complete when implementation choices fit the behavior and
checks, or a blocking question has an owner.

## Design a change

1. Define the caller's goal and inspect actual call sites, existing contracts,
   tests, and relevant architecture decisions. Capture the constraints and
   any questions that could affect the design.
2. For a consequential choice, compare two viable interfaces with a concrete
   call-site example for each. Assess what callers need to know, where future
   changes would land, and how to test behavior through the interface. Include
   failure and compatibility trade-offs when they affect the decision.
   Follow data and errors across the boundary. Prefer the design that makes
   callers simpler and keeps likely changes together. Add layers only for
   demonstrated responsibilities.
3. Recommend a design with evidence and name any uncertainty that could
   change it. Within a plan, capture the chosen design in the existing decision
   record and carry its constraints and verification into the spec and tasks.

Example: a retry helper could accept a raw request or a caller-supplied operation.
Compare real call sites, cancellation, error reporting and repeated side effects.
Choose the smallest interface that preserves the required behavior.

Avoid speculative extensibility, cosmetic module splitting and alternatives that
cannot meet the constraints. Design is complete when the selected interface has
usage/failure examples, compatibility consequences and a verification approach.

## Audit the existing architecture

1. Start in the requested area. Follow a recent or planned change through
   callers, tests, and dependencies to see where work spreads.
2. Identify candidates with concrete friction, such as repeat edits across
   call sites or behavior that can only be tested through fragile setup.
   Rank them by observed friction and the likelihood of future changes.
3. Return evidence, consequences, and a recommendation for the highest-value
   candidate. State what would justify revisiting any existing decision.
   Show the affected call path and the behavior that must survive the change.
   A readable before/after sketch is useful when it communicates the trade-off.
