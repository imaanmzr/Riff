# Riff

Riff is a small, model-independent workflow for taking software changes from
uncertain idea to reviewed implementation. It guides an agent through discovery,
research, decisions, specifications, task planning, implementation, verification,
and recovery across Codex, Cursor, VS Code with GitHub Copilot, and Claude Code.

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

## Install the terminal utility

### Windows

From the repository root, run this in PowerShell with Python 3.10 or newer.
The installer prints the actual launcher directory, including when Microsoft
Store Python redirects the installation.

```powershell
$riffBin = py -3 .\install_cli.py --print-bin-path
if ($LASTEXITCODE -ne 0) { throw 'Riff installation failed' }
$env:Path = "$riffBin;$env:Path"
riff --version
riff init
```

If Python is installed through the Microsoft Store, use `python3` or
`python` in place of `py -3`. The example enables `riff` for this terminal.
Follow the [Windows installation guide](docs/installation.md#windows) to
save the directory to your user PATH for future terminals.

### Linux and macOS

Run these commands from the repository root.

```bash
python3 install_cli.py
export PATH="$HOME/.local/bin:$PATH"
riff --version
riff init
```

Add the PATH line to your shell configuration for future terminals. You can also
install into a chosen prefix with `python3 install_cli.py --prefix /path/to/prefix`.
Re-running this installer updates the managed terminal utility.

With pipx available, the Python package can be installed directly from this checkout.

```bash
pipx install .
```

## Install

After installing the terminal utility, start the interactive setup:

```bash
riff init
```

The wizard asks which project and agent host to configure. It supports Codex,
Cursor, and Claude Code. It adds the skill to the host's project skill directory
and initializes `.engineering-workflow/` settings while preserving existing
project instructions and configuration.

You can provide values without prompts:

```bash
riff init --project /path/to/project --host codex
riff init --project /path/to/project --host cursor
riff init --project /path/to/project --host claude
```

For Cursor, Riff reuses an existing Codex or Claude skill installation when
available. To edit settings later, run `riff configure`. To update the
installed skill, run `riff update --host codex` with the project path
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

## Everyday commands

```bash
riff --help
riff doctor --host cursor
riff new refunds --title "Partial refunds" --route critical
riff prompt refunds --host cursor
riff status
riff validate refunds
```

Each command includes help through `riff COMMAND --help`. See the
[command reference](docs/commands.md) for execution validation, routing, JSON
status output, and prompts for resuming or reviewing work.

## Development

Riff uses Python's standard library. Run its regression tests from the repository
root:

```bash
python3 planning/tests/test_validate.py
python3 execution/tests/test_gates.py
python3 recovery/tests/test_state.py
python3 routing/tests/test_router.py
python3 distribution/tests/test_install.py
python3 distribution/tests/test_cli.py
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
