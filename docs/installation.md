# Installation and use

## Requirements

Python 3.9 or newer. Recovery uses Unix file locking. The host application must
support repository skills or allow an agent to read `SKILL.md` directly.

## Interactive setup

Extract the Riff release archive, open a terminal in its directory, and run:

```bash
./riff init
# or: python3 riff.py init
```

The CLI asks for a project path and one host: Codex, Cursor, or Claude Code. It
installs under `.agents/skills`, `.cursor/skills`, or `.claude/skills`. Cursor can
read the Codex and Claude paths too, and Riff reuses an existing installation.

The wizard asks for build/test commands and a task-record directory. It treats
commands as documentation and never executes them. Model IDs and concurrency
capabilities are optional. They must match the models and features exposed by
your active host. Leave mappings blank to disable routed dispatch.

Use `--project` and `--host` to avoid the initial questions:

```bash
python3 riff.py init --project /work/my-service --host claude
```

## Configure and update

```bash
python3 riff.py configure --project /work/my-service --host claude
python3 riff.py update --project /work/my-service --host claude
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

Use `$riff` in Codex and `/riff` in Cursor or Claude Code.

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
