# Install the Riff project skill

Python 3.10 or newer is required. The skill supports project installation for
Codex, Cursor, VS Code with GitHub Copilot, and Claude Code. Your host supplies
model access and agent tools.

## Install

From this distribution directory, choose the command for your host:

```bash
python3 riff.py init --project /path/to/project --host codex
python3 riff.py init --project /path/to/project --host cursor
python3 riff.py init --project /path/to/project --host vscode
python3 riff.py init --project /path/to/project --host claude
```

On Windows, use `py -3` or `python` in place of `python3`. The target project
must already exist. The setup wizard saves build/test commands as text; it does
not execute them. Canceling configuration leaves the skill installed.

The skill is installed under `.agents/skills/riff` for Codex,
`.cursor/skills/riff` for Cursor, `.github/skills/riff` for VS Code Copilot, or
`.claude/skills/riff` for Claude Code. Project settings live in
`.riff/`. Existing instruction files are preserved.

Cursor can also discover Codex and Claude skill paths. When either is already
installed, Riff directs you to use that copy and update it with its original
host rather than creating another Cursor copy.

For a `riff` command available across projects, run `install_cli.py` from the
full repository checkout. The full
[installation guide](https://github.com/imaanmzr/Riff/blob/HEAD/docs/installation.md)
includes platform-specific PATH instructions.

## Git visibility

During setup in a Git project, select `local`, `track`, or `unchanged`. You can
also pass `--git local` or `--git track` to `init`, or switch later:

```bash
python3 riff.py configure --project /path/to/project --git local
python3 riff.py configure --project /path/to/project --git track
```

Local mode uses Git's clone-local exclusions for the skill, settings, and the
entire configured task-record directory. Choose a dedicated records directory.
Tracking mode removes Riff's exclusions; other Git ignore rules still apply.

To stop tracking Riff files already in Git, add `--untrack` to
`configure --git local`. This stages removals from the index and retains working
copies. Inspect the staged changes before committing.

## Invoke the skill

Open the target project. Use `$riff` in Codex or `/riff` in Cursor, VS Code
Copilot, or Claude Code:

```text
$riff Design the retry interface.
$riff Update the setup docs.
$riff Plan the retry fix. Stop after plan review.
$riff Execute the reviewed plan at docs/work/retry-fix/.
$riff Resume the task at docs/work/retry-fix/.
```

If skill discovery is unavailable, ask the agent to read the installed
`SKILL.md` by path. See [host guidance](skills/riff/references/hosts.md) for model
selection and handoffs. Do not run two coordinators against the same task.

To use Riff by default, optionally add a reference to your project's existing
instruction file, substituting the path for your host:

```text
For planning, implementation, review, and recovery, follow
.agents/skills/riff/SKILL.md and scale the process to task risk.
```

The installer does not add this reference automatically.

## Configuration

The wizard writes these files in the target project:

- `.riff/project.json`: build/test commands, task-record
  directory, and project constraints.
- `.riff/routing-<host>.json`: model mappings, concurrency, and
  token budgets.
- `.riff/hosts/<host>.json`: declared host models and capabilities.

The CLI prefers host-specific routing and capability files and falls back to
shared `routing.json` and `host.json` when they are absent. Model mappings must
match the active host. Empty mappings disable routing; planning can still run in
the current agent. Token budgets guide assignments and do not cap provider bills.
Task records default to `docs/work/<task-id>/`.

Existing projects using only `.engineering-workflow/` keep using that directory
until you rename it to `.riff/`. No automatic move or merge is performed. If both
directories exist, resolve the duplicate while preserving your settings. Stop
active work before renaming, refresh older Git local exclusions with
`riff configure --git local`, and reconcile reviewed source fingerprints that
refer to the previous settings path.

## Update

```bash
python3 riff.py update --project /path/to/project --host claude
```

Use the same host as the original installation. Updates refuse locally modified
or unmanaged skill files; reconcile those edits first. The skill updates before
the configuration wizard opens. Answer `no` at `Save configuration?` to keep saved
settings. Run one installer or wizard per target project at a time.

The project skill remains usable after its installation source is moved or
removed. The CLI still needs this distribution directory or an installed copy.

## Remove

Delete `riff` from the skill directory used by your host. If Cursor uses an
existing Codex or Claude copy, remove that copy only when no host needs it.
Keep `.riff/` and task records to retain configuration and history.
Remove any instruction-file reference you added yourself.

## Verification and license

Regression tests cover installation paths and bundled references. Live workflow
sessions in Cursor and Claude Code have not been verified.
Riff is distributed under the [MIT License](LICENSE).
