# Recovery

Recovery saves local checkpoints and proposes how to reconcile interrupted work
or source changes. Read [WORKFLOW.md](WORKFLOW.md) before saving or resuming state.

## Use

From the target project, save a checkpoint using a JSON array of project-relative
file paths as the manifest:

```bash
riff checkpoint retry-fix --manifest source-files.json --expected-generation 0
riff reconcile retry-fix --manifest source-files.json
```

Generation `0` creates the first checkpoint. For later saves, use the generation
read from the current checkpoint. Stale writers are rejected. `reconcile` prints
a proposal for inspection without changing task state or replaying work.

To continue in an agent chat:

```text
$riff Resume the task at docs/work/retry-fix/.
```

Use `/riff` in Cursor, VS Code Copilot, or Claude Code. The agent must compare
saved state with the current repository, inspect interrupted work, and resolve
stale evidence before continuing. Prior authorization remains in effect.

## Checkpoints and boundaries

Checkpoints contain checksums, generation numbers, plan and execution records,
file fingerprints, and reconciliation history. Local locking and atomic file
replacement protect checkpoint writes on Windows and Unix.

Only manifest-listed paths are fingerprinted. Regenerate the inventory to detect
new files. Source drift conservatively blocks the run until affected work and
reviews are reconciled. A checksum establishes stored-content integrity; it does
not establish that task claims are true.

Recovery provides no distributed locking, automatic rollback, external-action
retries, or independent backups.

## Validation

From the repository root:

```bash
python3 recovery/tests/test_state.py
```

The suite covers stale writers, corrupt checkpoints, interrupted work, source
drift, and preservation of the prior checkpoint when replacement fails.
