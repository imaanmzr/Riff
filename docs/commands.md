# Riff commands

Run `riff --help` for the command list and examples. Every command has its own
help, such as `riff new --help`. Running `riff` without arguments displays help.

| Command | Purpose |
| --- | --- |
| `riff init` | Install the project skill and configure the project |
| `riff configure` | Edit build/test commands, model mappings and budgets |
| `riff update` | Update a project's skill using the installed Riff version |
| `riff doctor` | Inspect project settings and discover installed skill files |
| `riff new TASK` | Create draft planning records for a new task |
| `riff status [TASK]` | Show recorded plan/execution status and blocker counts |
| `riff prompt TASK` | Print the agent-chat prompt for a task |
| `riff validate TASK` | Validate the structure of plan.json |
| `riff route TASK --host HOST` | Propose dispatch assignments from saved records |

Commands accept `--project /path/to/project`. Setup commands prompt for a project
when it is omitted. Task and inspection commands use the current directory.
Supported hosts are `codex`, `cursor`, `claude`, and `vscode`.

## Start a task

```bash
riff init --host cursor
riff new refunds --title "Partial refunds" --route critical
riff prompt refunds --host cursor
```

`new` creates `plan.md` and a DRAFT `plan.json` in the configured task-record
folder. The initial route is provisional until the planning agent inspects
the task. A Git HEAD value is recorded if available. The planning agent still
needs to inspect uncommitted changes and define requirements. Task creation
refuses to overwrite an existing task. IDs may contain letters, digits,
underscores and hyphens, up to 80 characters.

Paste the prompt into your agent chat to start planning. Choose another operation
with `--action execute`, `--action resume`, or `--action audit`.

```bash
riff prompt refunds --host cursor --action execute
riff prompt refunds --host claude --action resume
```

`prompt` prints instructions for the host agent. Execution begins when you send
those instructions in the host.

## Inspect and validate

```bash
riff status
riff status refunds --json
riff doctor --host cursor
riff validate refunds
riff validate refunds --execution
```

Status reads saved records. Doctor checks local configuration and skill locations.
The active editor must confirm skill discovery and actual model access.
Plan validation checks structure, so a structurally valid DRAFT may pass. Use
execution validation to check readiness and execution evidence together. It reads
`plan.json` and `run.json` from the task folder. Preserve these filenames when
creating execution records. Validation failure returns a nonzero exit code.

## Route pending work

```bash
riff route refunds --host cursor
```

Routing reads the task's plan.json and run.json. It prefers host-specific
`routing-cursor.json` and `hosts/cursor.json` settings, falling back to the shared
routing.json and host.json. The output is a proposal for the coordinator to inspect
and dispatch using host tools. Missing input or failed gates prevent dispatch.

## Update the utility

To install a newer checkout of the terminal utility, run the
[installer for your platform](installation.md#install-the-terminal-utility)
from that checkout, or reinstall it with your Python package manager. Then use
`riff update` to update the skill in each project.
