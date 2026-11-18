# Riff

Riff is a local, model-independent workflow for taking software changes from
uncertain idea to reviewed implementation. It guides an agent through discovery,
research, decisions, specifications, task planning, implementation, verification,
and recovery across Codex, Cursor, VS Code with GitHub Copilot, and Claude Code.

The workflow is delivered as a repository skill and installed with a short CLI.
Plans, decisions, execution state, and evidence live with the project so another
agent session can resume the work.

## What it does

- **Research** — investigate a question, record sources and alternatives, and
  explain uncertainty in structured and readable reports.
- **Design & Architecture** — compare interfaces and prioritize architecture improvements.
- **Documentation** — review or update project docs based on what readers need to do.
- **Plan** — classify risk, inspect the codebase, gather evidence, record
  decisions, write acceptance criteria, and build a reviewed task plan.
- **Readable plans** — present summaries, decisions, acceptance checks, and task
  dependencies. Export Markdown or offline HTML with Mermaid diagrams, including
  authored flows and sequence diagrams.
- **Debug** — guide bounded reproduction and diagnosis, record hypotheses and
  actual results, and propose a fix for review.
- **Replan** — preserve earlier decisions and snapshots while revising tasks and
  invalidating stale reviews.
- **Execute** — dispatch dependency-ready tasks, verify changes, review them, and
  integrate work against the plan.
- **Recover** — checkpoint task state and identify stale decisions or reviews
  after interruption or code changes.
- **Route** — propose model/task assignments based on capability, scope overlap,
  concurrency, and token budgets.
- **Inspect** — show plans, explain blockers, compare snapshots, and check current
  evidence against saved status.
- **Configure** — use profiles for features, bugs, refactoring, migrations,
  documentation, architecture, and research. Inspect effective settings and
  change supported settings from the terminal.

New plans use schema v2 for requirements, acceptance checks, decisions, evidence,
and report references. Reviews bind to plan content, authored documents,
configuration, and source fingerprints. Existing plans remain readable, with
explicit migration available when you want the new record format.

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
Cursor, VS Code with GitHub Copilot, and Claude Code. It adds the skill to the
host's project skill directory and initializes `.engineering-workflow/` settings
while preserving existing project instructions and configuration.

Pass the project and host to skip those initial questions. The configuration
wizard still asks about project settings and whether to save them.

```bash
riff init --project /path/to/project --host codex
riff init --project /path/to/project --host cursor
riff init --project /path/to/project --host vscode
riff init --project /path/to/project --host claude
```

In a Git project, choose whether to keep Riff files local during setup. Use
`riff init --host codex --git local` to select local mode, or switch an existing
project with `riff configure --git local` or `riff configure --git track`.

For Cursor, Riff reuses an existing Codex or Claude skill installation when
available. To edit settings later, run `riff configure`. To update the
installed skill, run `riff update --host codex` with the project path
as prompted, or pass `--project /path/to/project`.

See [Installation and use](docs/installation.md) for setup, model configuration,
updates, and troubleshooting.

## Update an existing project

From the latest Riff checkout, re-run the CLI installer for your platform. Then
update the skill in each project using its configured host.

```bash
riff --version
riff update --project /path/to/project --host codex
```

The update installs the skill before opening the configuration wizard. Answer
`no` at `Save configuration?` to retain existing settings. Existing task records
stay in their current format. Use `riff migrate TASK` in the target project to
preview a schema upgrade. See [upgrading to 0.8.0](docs/installation.md#upgrade-to-080)
for platform commands and migration details.

## Use

Invoke the skill in the target project:

```text
$riff Design the refund retry interface.
$riff Audit architecture in the installer.
$riff Update the VS Code setup docs.
$riff Plan partial refunds. Stop after plan review.
$riff Execute the reviewed plan at docs/work/partial-refunds/.
$riff Resume the task at docs/work/partial-refunds/.
```

Use `/riff` in Cursor, VS Code Copilot, and Claude Code. Riff scales the
workflow from one compact task for a local fix to deeper verification and
review when uncertainty or consequences warrant it.

## Your first task

Run these commands in the project where you installed Riff. Choose a short ID
for the work, such as `refunds`, when you create it.

```bash
riff new refunds --title "Partial refunds"
riff plan --task refunds
```

`refunds` is the task ID. `Partial refunds` is its display title. Riff creates
`docs/work/refunds/plan.md` and `docs/work/refunds/plan.json` by default. Each task
has its own folder containing those filenames. The `plan` command prints a
prompt to paste into your agent chat. The agent fills in and reviews the plan.

Read or export that same task by its ID.

```bash
riff status
riff show refunds
riff render refunds --format html --output refunds.html
```

Open the exported `refunds.html` in your browser. The output filename is your
choice. To export Markdown instead, use `--format markdown --output refunds.md`.
You can render a draft to read it, and the export shows its current status.

The usual syntax is `riff COMMAND ARGUMENTS --option VALUE --flag`.
Options follow the command. `--format html` selects a value, while `--overwrite`
is a flag you add when replacing an existing export. Find all saved task IDs with
`riff status`. Use `riff render --help` for that command's options.

For a full explanation of IDs, folders, commands, and every supported option, see
the [command guide](docs/commands.md#command-syntax).

## Everyday commands

Riff 0.8 adds readable plans, offline HTML/Mermaid exports, explainable checks,
research/debug/replan workflows, profiles and explicit migration/recovery commands.
See [Readable plans and investigation workflows](docs/features.md) for examples.

```bash
riff --help
riff doctor --host cursor
riff design "Compare retry interfaces" --host cursor
riff docs "Update the setup guide"
riff new refunds --title "Partial refunds" --route critical
riff plan --task refunds --host cursor
riff status
riff validate refunds
riff show refunds
riff explain refunds
riff check refunds
riff render refunds --format html --output refunds.html
riff research "Compare retry strategies"
riff debug "Retries duplicate an action"
riff replan refunds --reason "New compatibility requirement"
```

Each command includes help through `riff COMMAND --help`. See the
[command reference](docs/commands.md) for execution validation, routing, JSON
status output, and prompts for resuming or reviewing work.

## Development

Riff selects engineering guides when the task needs them. Requirements/design,
debugging, implementation/testing, and review guidance help agents choose concrete
examples, investigate causes, and verify changed behavior. Small changes retain
compact plans. See [selective guidance and token usage](docs/features.md#token-usage-and-budgets).

Riff uses Python's standard library. Run its regression tests from the repository
root:

```bash
python3 planning/tests/test_validate.py
python3 execution/tests/test_gates.py
python3 recovery/tests/test_state.py
python3 routing/tests/test_router.py
python3 distribution/tests/test_install.py
python3 distribution/tests/test_cli.py
python3 planning/tests/test_records.py
python3 planning/tests/test_reports.py
python3 planning/tests/test_presentation.py
python3 distribution/tests/test_features.py
python3 routing/tests/test_adapters.py
python3 tools/sync_references.py --check
```

Read [Architecture](docs/architecture.md) for phase boundaries and current
limitations. See [Contributing](CONTRIBUTING.md) for changes and release work.

## Project status

Riff 0.8.0 has regression coverage for the CLI, records, workflows, recovery,
routing, and offline rendering. Release verification recorded 131 passed tests
and two Windows symlink tests skipped for missing privileges. Four local pilots
covered a small documentation plan, a feature plan, inconclusive research, and a
reproduced bug. Fresh wheel, standalone CLI, and skill installations were checked.

Human readability feedback and live sessions in Cursor and Claude Code remain
to be evaluated. Host adapter contracts currently use a simulated adapter.
Comparative token savings, provider cost, and quality improvements have not been
measured. See [release evidence](docs/work/riff-expansion/execution-log.md) and
[token usage](docs/features.md#token-usage-and-budgets).

## License

No license has been selected yet. Until one is added, do not assume the code is
licensed for reuse. Choose and add a license before publishing a public GitHub
repository if you want others to reuse it.
