# Installation and use

## Requirements

Python 3.10 or newer and a coding agent that supports project skills. Riff
includes installation paths for Codex, Cursor, VS Code with GitHub Copilot, and
Claude Code. An agent without skill discovery can read `SKILL.md` by path.

## Get the source

Clone the public repository before running the installation commands below:

```bash
git clone https://github.com/imaanmzr/Riff.git
cd Riff
```

If you downloaded a source archive instead, extract it and open a terminal in
the directory containing `install_cli.py`.

## Install the terminal utility

### Windows

Run from the repository root in Windows PowerShell 5.1 or newer. If your
Python command is `python3` or `python`, use it in place of `py -3` on
the first line.

```powershell
$riffBin = py -3 .\install_cli.py --print-bin-path
if ($LASTEXITCODE -ne 0) { throw 'Riff installation failed' }

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if (($userPath -split ';') -notcontains $riffBin) {
    $newPath = if ($userPath) { "$riffBin;$userPath" } else { $riffBin }
    [Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
}
if (($env:Path -split ';') -notcontains $riffBin) {
    $env:Path = "$riffBin;$env:Path"
}

riff --version
riff init
```

The script adds the installed `riff.cmd` directory to your user PATH for
future terminals and to the current PowerShell session. Microsoft Store
Python may redirect the installation into its package directory, so use
the directory reported by `--print-bin-path`.

If you already ran the installer and see “The term 'riff' is not recognized,”
run the block above to register the actual install directory. If you installed
with a custom `--prefix`, pass the same prefix on the first line. Rerun the
installer with that prefix to upgrade the CLI.

If Windows reports that a filename is too long, choose a shorter
`--prefix` or move the project closer to the drive root.

See [Uninstall](#uninstall) for the files to remove.

### Linux and macOS

Run from the repository root.

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

## Interactive setup

After installing the terminal utility, run:

```bash
riff init
```

The CLI asks for a project path and one host. It installs the skill under
`.agents/skills/riff` for Codex, `.cursor/skills/riff` for Cursor,
`.github/skills/riff` for VS Code Copilot, or `.claude/skills/riff` for Claude Code. Cursor can also discover the Codex and
Claude paths. If either copy is already installed, Riff directs you to use it
and update it with its original host instead of installing a duplicate.

The wizard asks for build/test commands and a task-record directory. It treats
commands as documentation and never executes them. Model IDs and concurrency
capabilities are optional. They must match the models and features exposed by
your active host. Leave mappings blank to disable routed dispatch.

Use `--project` and `--host` to avoid the initial questions:

```bash
riff init --project /work/my-service --host claude
```

## Git visibility

In a Git working tree, the wizard lets you keep Riff files local, make them
eligible for tracking, or leave the current behavior unchanged. You can also
select a mode explicitly.

```bash
riff init --host codex --git local
riff configure --git local
riff configure --git track
```

`local` adds repository-local Git exclusions for the Riff skill folders,
`.riff/`, and the entire configured task-record folder
(`docs/work/` by default). Choose a dedicated folder for task records.
The rules live in Git's `info/exclude` file. They stay in this clone and
also apply to linked worktrees of the same clone. Changing the task-record
folder keeps earlier local exclusions so old records stay local.

`track` removes Riff's exclusion rules. Other Git ignore rules still apply.
By default, switching modes preserves the Git index. To stop tracking files
that are already in Git, run this from the target project:

```bash
riff configure --git local --untrack
git diff --cached --name-status
```

This stages removals of the Riff skill, settings, and files belonging to tasks
in the current records folder. A task directory must contain a `plan.json`
or `plan.md`. The working copies stay on disk. Review and commit the staged
removals when you want the repository to stop tracking those files. Git can
refuse the operation if it would discard content that exists only in the
index.

## Configure and update

### Upgrade to 0.8.0

Update the terminal utility from your latest Riff checkout, then update the skill
in each target project. On Windows, run the following in PowerShell from the Riff
checkout, replacing the example project path and host with yours.

```powershell
$riffBin = python .\install_cli.py --print-bin-path
if ($LASTEXITCODE -ne 0) { throw 'Riff installation failed' }
& "$riffBin\riff.cmd" --version
& "$riffBin\riff.cmd" update --project "C:\repos\my-app" --host codex
```

On Linux or macOS, run from the latest checkout.

```bash
python3 install_cli.py
export PATH="$HOME/.local/bin:$PATH"
riff --version
riff update --project /path/to/my-app --host codex
```

Use your original `--prefix` if you installed the utility in a custom location.
The version should report `Riff 0.8.0`. The skill update completes before the
configuration wizard opens. Answer `no` at `Save configuration?` to retain your
saved settings. Reconcile any locally edited skill files before updating them.

To find saved task IDs and preview migrating one, run in the target project.

```bash
riff status
riff migrate refunds
```

Migration is optional. Applying `riff migrate refunds --apply` creates a backup,
upgrades `plan.json`, archives prior reviews, and returns the plan to DRAFT for
review. See [migration and recovery](features.md#compare-checkpoint-and-migrate).

### Change settings or refresh a project skill

```bash
riff configure --project /work/my-service --host claude
riff update --project /work/my-service --host claude
```

Riff preserves project settings and refuses to overwrite locally edited or
unmanaged installed skill files. Back up and reconcile local changes before
updating. The installer does not alter `AGENTS.md`, `CLAUDE.md`, or Cursor rules.
You can add a reference to the skill in the instruction file your team uses.

If you already installed the skill as `engineering-workflow`, run the update
command for that project. Riff replaces the previous installation if its files
match the installer manifest. Update any project instructions that reference
the old skill command or path.

New projects store configuration in `.riff/`. Existing projects with only
`.engineering-workflow/` remain supported, including configuration writes and
skill updates. To adopt the new name, stop active Riff work and rename that
directory to `.riff/`. Riff does not move or merge settings automatically; if
both names exist, preserve your files and resolve the duplicate before running
configuration commands. Reviewed plans that fingerprint the old settings path
need the usual freshness review/reconciliation after a manual rename.
Git local mode covers both names; rerun `riff configure --git local` to refresh
exclusions after renaming a project configured with an older Riff version.

## Invoke

Use `$riff` in Codex and `/riff` in Cursor, VS Code Copilot, or Claude Code.

```text
$riff Design the return policy interface.
$riff Audit architecture in the installer.
$riff Update the VS Code setup docs.
```

Design and architecture audits are read-only by default. Ask for a docs edit
explicitly when you want one. Riff keeps small tasks compact and adds planning,
verification, and review as the task's uncertainty or risk increases.

```text
$riff Plan the new return flow. Stop after the plan review.
/riff Plan the new return flow. Stop after the plan review.
```

After reviewing the plan, authorize execution explicitly.

```text
$riff Execute the reviewed return-flow plan in docs/work/returns/.
/riff Execute the reviewed return-flow plan in docs/work/returns/.
```

Resume from another app by asking it to resume the task record. Do not run two
coordinators against the same task at once.

## Model settings

`.riff/routing-<host>.json` maps capability profiles to model
IDs. `.riff/hosts/<host>.json` records capabilities the host
makes available. The CLI asks these details only when configuring routing.
These values do not grant provider access. Select the main model in the host UI.

## Uninstall

Remove the installed `riff` folder from the host's `.agents/skills`,
`.cursor/skills`, `.github/skills`, or `.claude/skills` directory. Keep
`.riff/` and task records if you want to retain configuration
and history. Remove any instruction-file reference you added yourself.

For a CLI installed with `install_cli.py`, remove only these managed paths under
the prefix used at installation:

- `bin/riff` on Linux/macOS or `bin/riff.cmd` on Windows.
- `lib/riff-workflow/`.

The default prefix is `~/.local` on Linux/macOS and `%LOCALAPPDATA%\Riff` on
Windows. For Microsoft Store Python, use the actual path printed by the installer.
Remove a PATH entry only if you added it for Riff and no other tools use it.
For a pipx installation, run `pipx uninstall riff-workflow`.

## VS Code with GitHub Copilot

```bash
riff init --project /path/to/project --host vscode
```

The installer adds `.github/skills/riff/SKILL.md`. Invoke `/riff` in Copilot
Chat and include the operation, such as `/riff Plan this feature`. VS Code support
here refers to GitHub Copilot's Agent Skills integration.

## Terminal commands and agent commands

`riff init`, `riff configure`, and `riff update` manage project setup.
`$riff` in Codex and `/riff` in the other supported agent chats start the
engineering workflow. Model access and subagents are supplied by the selected host.

See the [command reference](commands.md) for task creation, progress, validation,
and routing commands.
Start with [command syntax and task IDs](commands.md#command-syntax) for an
explanation of positional arguments, flags, folders, and rendering.
