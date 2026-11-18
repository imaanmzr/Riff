# Implement in testable slices

Use this guide during authorized execution. Follow the plan's
[route rubric](../planning/WORKFLOW.md#route-rubric) and the
[execution workflow](WORKFLOW.md) for evidence, review, and integration.

Consult this guide for behavior changes. A clear copy change can use its focused
verification directly. Use established project tests and tools before adding any.

## Choose useful evidence

1. Identify the observable behavior and the interface that exposes it. Choose a
   test boundary that exercises the actual failure or user action. Use the plan's
   acceptance checks and project conventions to decide scope without an extra
   approval round for routine test choices.
2. Prefer a failing regression test before fixing a bug. Verify that it fails for
   the reported reason. For a feature, use a small test-first slice when it helps
   establish behavior. When this is impractical, record why and use concrete
   alternative evidence, such as a reproducible command or inspected UI result.
3. Keep expected results independent of the implementation. Assert observable
   outputs, errors and required side effects. Include relevant absence of effects,
   such as no write after validation fails. Mock external dependencies at stable
   boundaries when needed; excessive internal mocks often conceal integration bugs.

Example: a quantity parser accepts a positive integer and rejects zero. Assert
that `parse_quantity("2")` returns `2`, and `parse_quantity("0")` raises the
specified error. Computing the expected result with the parser itself cannot
catch a defect. Testing only that a result exists misses the boundary case.

## Deliver one behavior at a time

1. Build the narrowest complete path through the affected layers. Run the focused
   check, make the necessary change, and inspect its result before the next slice.
   Keep setup and feedback fast enough to run after a meaningful edit.
2. Refactor when observed duplication or complexity makes the change harder.
   Rerun the same behavioral checks. For coupled migrations, introduce the new
   form alongside the old, migrate callers in compatible batches, then remove
   the old form after verifying callers and rollback requirements.
3. Run required project checks and inspect the final diff. Use
   [review guidance](REVIEW.md) at the workflow's review stage. Bind actual checks
   and reviews to the candidate using the existing execution record.

Common mistakes include writing a large imagined test suite before learning from
one slice, asserting private helper calls, weakening assertions to make them pass,
and treating a skipped check as success. A passing check should be capable of
failing for the defect it claims to cover.

The slice is complete when its acceptance behavior and relevant failure cases
have actual verification evidence, required checks pass, and the review required
by the route has accepted the current candidate. Keep unresolved evidence visible.
