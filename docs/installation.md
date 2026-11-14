# Installation and use

## Requirements

Python 3.10 or newer. The host application must support repository skills or
allow an agent to read `SKILL.md` directly.

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

To remove the CLI, delete its install directory and remove its `bin` entry
from your user **Path**.

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

The CLI asks for a project path and one host: Codex, Cursor, VS Code with GitHub Copilot, or Claude Code. It
installs under `.agents/skills`, `.cursor/skills`, or `.claude/skills`. Cursor can
read the Codex and Claude paths too, and Riff reuses an existing installation.

The wizard asks for build/test commands and a task-record directory. It treats
commands as documentation and never executes them. Model IDs and concurrency
capabilities are optional. They must match the models and features exposed by
your active host. Leave mappings blank to disable routed dispatch.

Use `--project` and `--host` to avoid the initial questions:

```bash
riff init --project /work/my-service --host claude
```

## Configure and update

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
the old skill command or path. Project configuration still lives in
`.engineering-workflow/`.

## Invoke

Use `$riff` in Codex and `/riff` in Cursor, VS Code Copilot, or Claude Code.

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

`.engineering-workflow/routing-<host>.json` maps capability profiles to model
IDs. `.engineering-workflow/hosts/<host>.json` records capabilities the host
makes available. The CLI asks these details only when configuring routing.
These values do not grant provider access. Select the main model in the host UI.

## Uninstall

Remove the installed `riff` folder from the host's `.agents/skills`,
`.cursor/skills`, or `.claude/skills` directory. Keep `.engineering-workflow/`
and task records if you want to retain configuration and history.

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
