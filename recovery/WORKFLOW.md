# Recovery 0.3

Use for save/checkpoint, handoff, interruption, and resume requests. Read planning
and execution workflows. Preserve authorization already given; do not mistake a
checkpoint's boolean for new permission. Never replay external actions on resume.

## Capture
After each meaningful transition and before handoff, save plan, execution record,
source manifest and artifact references. Include source files, build configuration,
contracts and relevant evidence files in a JSON array of relative paths. Use full
repo file inventory (excluding generated output, secrets and recovery state) when
possible; include untracked source. The fingerprint tool hashes only explicitly
listed files, not a recursive discovery. Regenerate the inventory on resume to
catch additions. Never put checkpoint files in their own manifest.

Use state.py checkpoint with actual plan/run, root, manifest, state and expected
generation (0 for initial creation). Subsequent saves must use the generation read
by this coordinator. Concurrent stale saves fail. Stop on corruption; preserve
the damaged file and recover from an independently verified backup if available.
Do not silently reset generation or discard checkpoints. Local locking and atomic
replacement protect one checkpoint file; they are not a distributed transaction.

## Resume
1. Read current instructions, saved plan, task records and evidence. Inspect live
   agents and worktrees; do not launch duplicate work while an agent may remain
   active. Reconcile any external operation through its actual recorded outcome.
   Use `riff status TASK --details` for the generated current handoff rather than
   assuming an older authored next-action sentence is still current. Recorded
   task/review states and computed readiness still require inspection of evidence.
2. Rebuild the source/evidence manifest and run state.py resume. It emits a
   proposed reconciled checkpoint to stdout; it never writes or executes changes.
3. Compare plan content even when its author forgot to increment the revision.
   Any plan/source drift conservatively blocks all tasks and archives evidence.
   Interrupted running tasks become blocked. Unchanged integrated work remains
   integrated. Do not equate old success with current correctness.
4. Inspect the proposal and actual work. For interruption, determine whether the
   change exists, checks finished, side effects occurred, and the original agent
   stopped. Adopt verified work or continue it; do not automatically rerun.
5. For design drift, revise and review the plan, rebind the execution baseline,
   reconcile added/removed tasks, and recheck affected candidates. Restore prior
   evidence only after proving applicability. Never just relabel old revisions.
6. Record resolution evidence, clear only resolved blockers, and transition tasks
   to pending, review or integrated according to execution gates. Run all relevant
   gates before dispatch. Persist reconciled state through the checkpoint command
   using the generation originally read. Preserve the history of invalidation.
7. Report completed work, stale/blocked work, unresolved decisions and next task.

## Commands
The main CLI exposes `riff checkpoint TASK --manifest PATH --expected-generation N`
and `riff reconcile TASK --manifest PATH`. The latter prints a proposal only.
Never silently reload and retry a stale generation. v2 checkpoints capture live
authored/config digests; resume compares them even if JSON revisions did not move.

python3 recovery/state.py checkpoint --state STATE --plan PLAN --run RUN --root REPO --manifest MANIFEST --expected-generation 0
python3 recovery/state.py resume --state STATE --plan PLAN --root REPO --manifest MANIFEST

All capitalized names are paths. A resume proposal contains the run under `run`;
use its reconciled run and history when saving, rather than the stale pre-resume
run. Keep raw proposal as evidence. The checkpoint command archives its prior
saved run; the proposal documents individual invalidations.

## Limits
No exactly-once effects, automatic rollback, background scheduler, worktree
reconstruction, or independent backup is claimed. Evidence existence and meaning
still require inspection. User code is never changed by the recovery utility.
