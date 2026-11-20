# Architecture

Riff consists of a project skill, a Python CLI, and four workflow modules. The
agent host supplies model access and tools. Riff supplies instructions, record
formats, validators, and local inspection utilities.

## Source layout

- `planning/`: discovery, requirements, design, research, debugging, and plan review.
- `execution/`: execution records, verification and review gates, and integration.
- `recovery/`: checkpoints, file fingerprints, and reconciliation proposals.
- `routing/`: capability mappings, task conflicts, concurrency, and budget checks.
- `planning/riff_core/`: shared record, configuration, storage, and presentation code.
- `distribution/`: CLI, installer, skill bundle, and offline rendering assets.

The root `riff` launcher and `riff.py` entry point load `distribution/riff.py`.
`install_cli.py` installs a standalone CLI. `distribution/install.py` installs
or updates the project skill in the selected host's skill directory.

## Canonical and installed code

The canonical workflow modules and Python core are copied into
`distribution/skills/riff/references/`. The installed CLI and standalone skill
utilities load that bundled core. Use `tools/sync_references.py` after changing
canonical sources and `--check` to detect drift.

The Python runtime uses the standard library. HTML exports embed the pinned
browser libraries in `distribution/assets/` and need no server or network access.
Their versions, checksums, and licenses are recorded with the assets.

## Project state

Configuration lives in `.engineering-workflow/` in the target project. Task
records default to `docs/work/<task-id>/`:

- `plan.md`: the authored specification and explanation.
- `plan.json`: requirements, acceptance checks, decisions, dependencies, evidence,
  and plan reviews.
- `run.json`: assigned agents, execution state, candidate revisions, checks,
  reviews, and integrated revisions.
- `checkpoint.json`: a checksummed snapshot with a generation number, file
  fingerprints, and reconciliation history.

Schema v2 binds plan reviews to authored documents, behavioral configuration,
and source fingerprints. A recorded READY status can become stale when those
inputs change. Legacy plans remain readable; explicit migration backs up the
original record, replaces `plan.json`, and returns the plan to DRAFT for review.
See [Record contracts](../planning/RECORDS.md).

Routing reads the plan and execution records with host capability and budget
settings. It proposes assignments; the coordinator checks the proposal and uses
host tools to dispatch work.

## Handoffs and limits

A new agent session must inspect current instructions, source, saved state, and
verification evidence before continuing. Checkpoints record previous state;
they do not establish that the current working tree matches it. Reconciliation
prints a proposal for the coordinator to inspect and adopt.

Only manifest-listed paths are fingerprinted. Regenerate the inventory to detect
new files. Locking is local to checkpoint writes; there is no shared database or
distributed scheduler. Run one coordinator per task.

Validators inspect declared records and source bindings. They do not authenticate
reviewers, run recorded tests, or prove semantic correctness. Routing does not
invoke provider APIs or enforce billing limits. The simulated adapter tests the
dispatch contract; it cannot supply qualifying execution or review evidence.
