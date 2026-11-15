# Implement in testable slices

Use this guide during authorized execution. Follow the plan's
[route rubric](../planning/WORKFLOW.md#route-rubric) and the
[execution workflow](WORKFLOW.md) for evidence, review, and integration.

1. Pick the smallest behavior that can be demonstrated through the normal
   entry point. Find an existing interface where a check can exercise it.
   For a behavioral bug, reproduce the reported symptom with a focused check
   before fixing it when feasible. Record any limit on reproduction.
2. Make the scoped change and rerun the focused check as it develops. Inspect
   the diff and verify the promised behavior. For a coupled migration that
   cannot land in one working slice, introduce a compatible form, migrate
   callers in safe batches, then retire the old form.
3. For a small task, use one compact record and labeled self-review. For
   larger tasks, use the focused feedback for each slice and verify the
   cross-boundary and failure behavior called for by the route. Record
   required checks and reviews for the candidate and verify the final
   integrated revision under the execution workflow.
