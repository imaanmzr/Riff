# Design & Architecture

Use this guide for an interface design, a consequential design choice during
planning, or an architecture audit. Apply the [route rubric](WORKFLOW.md#route-rubric)
to decide how much investigation the request warrants. Standalone design
and audit requests are read-only by default.

## Design a change

1. Define the caller's goal and inspect actual call sites, existing contracts,
   tests, and relevant architecture decisions. Capture the constraints and
   any questions that could affect the design.
2. For a consequential choice, compare two viable interfaces with a concrete
   call-site example for each. Assess what callers need to know, where future
   changes would land, and how to test behavior through the interface. Include
   failure and compatibility trade-offs when they affect the decision.
3. Recommend a design with evidence and name any uncertainty that could
   change it. Within a plan, capture the chosen design in the existing decision
   record and carry its constraints and verification into the spec and tasks.

## Audit the existing architecture

1. Start in the requested area. Follow a recent or planned change through
   callers, tests, and dependencies to see where work spreads.
2. Identify candidates with concrete friction, such as repeat edits across
   call sites or behavior that can only be tested through fragile setup.
   Rank them by observed friction and the likelihood of future changes.
3. Return evidence, consequences, and a recommendation for the highest-value
   candidate. State what would justify revisiting any existing decision.
