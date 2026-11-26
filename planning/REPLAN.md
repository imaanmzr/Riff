# Revise a plan without losing its history

`riff replan TASK --reason "CHANGE"` prints a prompt. It does not mutate a task,
invalidate reviews, or resume execution by itself. The invoked agent follows
[planning](WORKFLOW.md), [execution](../execution/WORKFLOW.md), and
[recovery](../recovery/WORKFLOW.md).

1. **Inspect the baseline.** Read the reviewed plan and authored artifacts, source
   manifest, configuration provenance, execution records, checkpoints, active
   agents, and worktrees. Identify actual changes and external side effects.
   Prevent duplicate work; stop dependent dispatch while its contract is changing.
   Use [Shared questioning](INTERVIEW.md); reuse earlier answers and reopen only
   decisions affected by changed intent/evidence, explaining the reason.
2. **Record why.** State the new evidence or changed product intent, requested
   scope, affected requirements, and existing authorization. Do not infer broader
   execution, publication, or deployment authority from a replan request.
3. **Preserve the old plan.** Save an immutable task-local snapshot of the prior
   JSON, authored artifacts, and evidence references before replacing them. Use a
   unique revision directory under `snapshots/`; refuse overwriting an existing
   snapshot. Record its content hashes. Preserve superseded decisions with IDs,
   reasons, and replacement references rather than deleting their history.
4. **Revise deliberately.** Update the structured requirements, decisions, checks,
   tasks, dependencies, authored specification, and traceability. Increment the
   plan revision, mark DRAFT, reassess route, and archive invalidated reviews.
   Re-resolve and freeze behavior-affecting configuration. Update the source and
   artifact manifests with actual hashes, not labels such as `latest`.
5. **Reconcile existing work.** If execution exists, generate a recovery proposal.
   Changes conservatively invalidate the run until evidence establishes what can
   be retained. Inspect task additions/removals, candidate changes, completed
   side effects, and active reservations. Do not just relabel old reviews or
   copy them to the new revision. Keep reconciliation evidence and checkpoint
   using the caller-observed generation; stale writes fail without auto-retry.
6. **Review the new revision.** Obtain the review required by the reassessed route.
   Bind it to the current plan content, authored artifacts, source baseline, and
   behavioral configuration. Resolve blockers before READY. Review independence
   is an actual separate session, not a fabricated identity field.
7. **Stop at the requested boundary.** Report the change, preserved snapshot,
   invalidated evidence, remaining uncertainty, and next task. Replanning never
   automatically resumes execution. Existing execution authority persists only
   within its original scope and only after current execution/recovery gates pass.

Write `reports/REPLAN1.md` and `reports/REPLAN1.json` using the templates. Record
reason, baseline/target revisions, source revision, snapshot, changed items,
superseded decisions, affected tasks, invalidated review references, reconciliation
reference, next action, and linked requirement/decision IDs. Register the JSON
report in plan `reports` and both report files in `reviewed_artifacts`. Review the
completed report together with the changed plan, not as a substitute for it.

`riff diff TASK --against SNAPSHOT` can expose structural and prose differences.
Textual differences do not establish semantic equivalence or prove that prior
evidence remains applicable.
