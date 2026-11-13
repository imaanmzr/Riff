# Riff

Riff is a small, model-independent workflow for taking software changes from
uncertain idea to reviewed implementation. It guides an agent through discovery,
research, decisions, specifications, task planning, implementation, verification,
and recovery across Codex, Cursor, and Claude Code.

The workflow is delivered as a repository skill and installed with a short CLI.
Plans, decisions, execution state, and evidence live with the project so another
agent session can resume the work.

## What it does

- **Plan** — classify risk, inspect the codebase, gather evidence, record
  decisions, write acceptance criteria, and build a reviewed task plan.
- **Execute** — dispatch dependency-ready tasks, verify changes, review them, and
  integrate work against the plan.
- **Recover** — checkpoint task state and identify stale decisions or reviews
  after interruption or code changes.
- **Route** — propose model/task assignments based on capability, scope overlap,
  concurrency, and token budgets.

Riff provides instructions and local validation utilities. The active agent host
provides model access, tools, and any subagent execution. Riff does not itself
call provider APIs or launch models.

## Install

Download and extract a Riff release, then run the interactive setup from its
folder:

```bash
./riff init
# or: python3 riff.py init
```

The wizard asks which project and agent host to configure. It supports Codex,
Cursor, and Claude Code. It adds the skill to the host's project skill directory
and initializes `.engineering-workflow/` settings while preserving existing
project instructions and configuration.

You can provide values without prompts:

```bash
python3 riff.py init --project /path/to/project --host codex
python3 riff.py init --project /path/to/project --host cursor
python3 riff.py init --project /path/to/project --host claude
```

For Cursor, Riff reuses an existing Codex or Claude skill installation when
available. To edit settings later, run `python3 riff.py configure`. To update the
installed skill, run `python3 riff.py update --host codex` with the project path
as prompted, or pass `--project /path/to/project`.

See [Installation and use](docs/installation.md) for setup, model configuration,
updates, and troubleshooting.

## Use

Invoke the skill in the target project:

```text
$riff Plan partial refunds. Stop after plan review.
$riff Execute the reviewed plan at docs/work/partial-refunds/.
$riff Resume the task at docs/work/partial-refunds/.
```

Use `/riff` in Cursor and Claude Code.

## Development

Riff uses Python's standard library. Run its regression tests from the repository
root:

```bash
python3 planning/tests/test_validate.py
python3 execution/tests/test_gates.py
python3 recovery/tests/test_state.py
python3 routing/tests/test_router.py
python3 distribution/tests/test_install.py
```

Read [Architecture](docs/architecture.md) for phase boundaries and current
limitations. See [Contributing](CONTRIBUTING.md) for changes and release work.

## Project status

Riff is an early, local-first tool. The workflow and installer have regression
tests. Real feature pilots and live sessions in Cursor and Claude Code remain to
be evaluated. Model routing produces a dispatch proposal for the active host.
It does not measure provider cost or guarantee that a model was actually used.

## License

No license has been selected yet. Until one is added, do not assume the code is
licensed for reuse. Choose and add a license before publishing a public GitHub
repository if you want others to reuse it.
