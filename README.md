# Riff

[MIT license](LICENSE) · [Installation](docs/installation.md) ·
[Commands](docs/commands.md) · [Contributing](CONTRIBUTING.md)

Riff is a local workflow and CLI for planning, implementing, reviewing, and
resuming software changes with coding agents. It supports project skills for
Codex, Cursor, VS Code with GitHub Copilot, and Claude Code.

Plans, decisions, checks, and execution state stay in your project as Markdown
and JSON. An agent can use those records to continue work in a later session or
another supported host.

## Quick start

You need Python 3.10 or newer, Git, and a supported coding agent. Clone Riff:

```bash
git clone https://github.com/imaanmzr/Riff.git
cd Riff
```

On Linux or macOS, install the CLI:

```bash
python3 install_cli.py
export PATH="$HOME/.local/bin:$PATH"
riff --version
```

Add the PATH line to your shell configuration for future terminals.

On Windows, run in PowerShell:

```powershell
$riffBin = py -3 .\install_cli.py --print-bin-path
if ($LASTEXITCODE -ne 0) { throw 'Riff installation failed' }
$env:Path = "$riffBin;$env:Path"
riff --version
```

Use `python` or `python3` in place of `py -3` if needed. See the
[installation guide](docs/installation.md) for persistent Windows PATH setup,
a custom installation prefix, and installation with pipx.

Next, install the skill in the project where you want to use it:

```bash
riff init --project /path/to/your/project --host codex
```

Choose `codex`, `cursor`, `vscode`, or `claude` for `--host`. The setup wizard
saves project settings under `.riff/` and lets you choose whether
to keep Riff files local to your Git clone or track them with the project.
Existing project instruction files are preserved.

## Plan and implement a change

Run these commands from your target project's root:

```bash
riff new retry-fix --title "Fix duplicate retries" --profile bug
riff plan --task retry-fix --host codex
```

`new` creates `docs/work/retry-fix/plan.md` and `plan.json`. `plan` prints a prompt
to paste into your coding agent's chat. The agent investigates the request,
writes the plan, and completes the review required by the task's risk.

Inspect the saved plan:

```bash
riff show retry-fix
riff explain retry-fix
riff check retry-fix
riff render retry-fix --format html --output retry-fix.html
```

Open `retry-fix.html` in a browser to read the plan offline. Drafts can be
exported too; `check` reports missing evidence until the plan is ready.

When you want the agent to implement the reviewed plan, generate an execution
prompt and send it in the agent chat:

```bash
riff execute retry-fix --host codex
```

Workflow commands print prompts. They do not call a model or start agent work
from the terminal.

You can also invoke the skill directly in chat. Use `$riff` in Codex and `/riff`
in Cursor, VS Code Copilot, or Claude Code:

```text
$riff Plan a fix for duplicate retries. Stop after plan review.
$riff Execute the reviewed plan at docs/work/retry-fix/.
$riff Resume the task at docs/work/retry-fix/.
```

## What Riff provides

- **Planning:** code investigation, requirements, design decisions, acceptance
  checks, task dependencies, and review before implementation.
- **Implementation and review:** task records tied to source revisions, checks,
  and review evidence. Small local changes use a compact plan and self-review;
  higher-risk work requires independent review.
- **Research and debugging:** prompts and record formats for comparing options,
  testing hypotheses, and recording results and unresolved questions.
- **Inspection and exports:** readable plans, readiness explanations, snapshot
  comparisons, and offline HTML with Mermaid diagrams.
- **Recovery:** checkpoints and file fingerprints that help an agent identify
  interrupted work or evidence made stale by source changes.
- **Routing:** proposed task and model assignments based on configured host
  capabilities, file conflicts, concurrency, and token budgets.

See [features and examples](docs/features.md) for profiles, migration, recovery,
and budget accounting. Use `riff --help` or `riff COMMAND --help` for CLI usage.

## Update

Update your Riff checkout and rerun `install_cli.py` using the same installation
prefix. Then refresh each project's skill:

```bash
riff update --project /path/to/your/project --host codex
```

The skill is updated before the configuration wizard opens. Answer `no` at
`Save configuration?` to retain existing settings. Updates refuse to overwrite
locally edited skill files. See the [upgrade guide](docs/installation.md#upgrade-to-080)
for platform commands and optional task-record migration.

## Scope and limitations

Riff runs locally and uses Python's standard library. It includes no provider API
integration, background scheduler, or automatic retry engine. Routing budgets
guide assignments; they do not cap provider billing.

Validators check record structure, source fingerprints, and review bindings.
They cannot establish that a review was independent or that a change is correct.
The coordinator must inspect the underlying code and evidence.

Installer and regression tests cover the supported host paths. Live workflow
sessions in Cursor and Claude Code have not been verified. The bundled host
adapter is a simulation for contract testing. Token savings, cost reductions,
and quality improvements have not been measured.

## Documentation and development

- [Installation](docs/installation.md): setup, configuration, updates, and removal.
- [Command reference](docs/commands.md): task IDs, options, and end-to-end examples.
- [Features](docs/features.md): exports, investigations, profiles, and recovery.
- [Architecture](docs/architecture.md): source layout, records, and phase boundaries.
- [Contributing](CONTRIBUTING.md): development checks and release verification.
- [Changelog](CHANGELOG.md): release history.

## License

Riff is licensed under the [MIT License](LICENSE). Bundled rendering libraries
retain their own MIT notices; see [asset provenance](distribution/assets/README.md).
