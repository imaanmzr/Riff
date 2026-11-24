# Riff commands

This reference covers Riff 1.0.0-rc.1. See [Readable plans and investigation
workflows](features.md) for detailed examples of exports, profiles, and reports.

Run `riff --help` for the command list and examples. Every command has its own
help, such as `riff new --help`. Running `riff` without arguments displays help.

## Command syntax

Most commands have this form. Words in CAPITALS below are placeholders for your
values. Square brackets mean an optional argument. Type the values themselves,
with quotes around text or paths containing spaces.

```text
riff COMMAND ARGUMENTS --option VALUE --flag
```

For example, this exports a saved task as an HTML file.

```bash
riff render refunds --format html --output refunds.html
```

| Part | Meaning in this example |
| --- | --- |
| `riff` | The installed terminal program |
| `render` | The command to run |
| `refunds` | The saved task ID, supplied as a positional argument |
| `--format html` | An option and its selected value |
| `--output refunds.html` | An option and the file path to create |

A flag switches behavior without taking a value. For example, `--overwrite`
allows replacing an existing export. Options belong after the command. Use
`riff --version` for the program version and `riff --help` for the command list.
Every command supports `--help`, including `riff config show --help` for a nested
command. Options are specific to each command.

## Task IDs, plan files, and locations

You assign the ID when creating a task.

```bash
riff new refunds --title "Partial refunds"
```

Here `refunds` is the task ID and `Partial refunds` is the display title. The ID
must start with a letter or digit and contain 1–80 letters, digits, underscores,
or hyphens. Keep the same spelling and capitalization in later commands.

With the default settings this creates the following files in your project.

```text
your-project/
  .riff/
    project.json
  docs/
    work/
      refunds/
        plan.md
        plan.json
```

`plan.md` contains the readable explanation. `plan.json` contains structured
records. Execution later uses `run.json` in the same folder. Every saved task
uses these filenames, with its ID distinguishing its directory. For instance,
`riff render refunds ...` reads the records in `docs/work/refunds/`. Supplying
`plan.md`, its full path, the title, or an internal implementation step such as
`T1` will not select that task. Internal `T1`/`T2` IDs identify steps inside its plan.

The directory prefix comes from `artifacts_directory` in
`.riff/project.json`, which setup normally sets to `docs/work`.
`riff config show` displays this saved project setting. Run `riff status` to
list saved task IDs, including records created by an agent. Ask the agent to save
its work in that configured directory with both `plan.md` and `plan.json` so the
CLI can find it. A standalone Markdown plan needs structured task records before
these commands can use it.

Run task commands from the project root, or supply the project root explicitly.
The CLI uses the current directory when `--project` is omitted.

```powershell
riff status --project "C:\repos\my-app"
riff render refunds --project "C:\repos\my-app" --format html --output "C:\exports\refunds.html"
```

The output directory must already exist. A relative `--output` path is resolved
from your terminal's working directory, including when you supply `--project`.
Input file options such as `--manifest` and `--against` also use the terminal's
working directory. Use absolute paths when running outside the project.

## A complete example

After installing the CLI, open a terminal in your target project.

```bash
riff init --host codex
riff new refunds --title "Partial refunds" --profile feature
riff plan --task refunds --host codex
```

Finish the setup wizard. Copy the output from `riff plan` into the agent chat
open on that project. Let the agent investigate, write the specification and
complete the required plan review. Then inspect the saved result.

```bash
riff status
riff show refunds
riff explain refunds
riff check refunds
riff render refunds --format html --output refunds.html
```

`check` reports missing requirements or evidence while a plan is still a draft.
Rendering is available for drafts too. Open `refunds.html` in a browser to read
the plan and its current evaluation. When you authorize implementation, generate
the execution prompt and send it in your agent chat.

```bash
riff execute refunds --host codex
```

Use your host name in place of `codex` where appropriate.

## Current status

```bash
riff status
riff status refunds
riff status refunds --details
riff status refunds --json
```

The default evaluates current evidence and shows each plan's route/revision/schema,
recorded and evaluated readiness, execution authorization, task progress, current
reviews, blockers and next action. A selected task lists all of its implementation
tasks; `--details` adds review history, candidate revisions and full gate findings.
Current-candidate reviews and checks are separated from historical or unbound
records. Integrated counts describe recorded task states, not independently proven
product correctness. `status` returns nonzero for unreadable records; use `check`
when an automation needs a nonzero exit for blocked or unknown readiness.

JSON remains an array with the existing `task`, `plan_status`, `execution_status`
and `blockers` fields. Additions include `progress`, `tasks`, `reviews`,
`evaluation`, `phase`, `next_action`, `next_command` and `next_command_argv`.
The same current action appears in `show`, `explain` and generated exports.
Inspection never edits the reviewed plan, migrates records or starts agent work.

## Migration guidance

```bash
riff migrate old-task
riff migrate old-task --manifest source-files.json
riff migrate old-task --apply --manifest source-files.json
```

Migration keeps its JSON result and adds `guidance.remaining_errors` and concrete
`next_steps`. The optional manifest is a nonempty JSON array of project-relative
source files, such as `["src/service.py", ".riff/project.json"]`. It captures
actual source, authored and effective-configuration fingerprints during a legacy
upgrade. It rejects traversal and self-binding to plan/run/checkpoint state.
Preview writes nothing; apply backs up the exact old plan and leaves DRAFT with
old reviews archived. Complete missing requirements/checks, obtain current review,
and reconcile old execution/checkpoints before resuming. Already-v2 binding changes
belong in a reviewed replan.

## Render options

```text
riff render TASK --output PATH [--format markdown|html]
            [--detail concise|full] [--diagrams auto|none]
            [--overwrite] [--project PATH]
```

| Argument or option | Meaning and default |
| --- | --- |
| `TASK` | Required saved task ID, such as `refunds` |
| `--output PATH` | Required destination file. Choose a path outside task records and settings |
| `--format markdown` | Produce Markdown. This is the default |
| `--format html` | Produce a self-contained HTML file for your browser |
| `--detail concise` | Show a summary and the first three findings |
| `--detail full` | Include the authored specification and detailed evidence |
| `--diagrams auto` | Include generated task diagrams and render authored Mermaid in HTML |
| `--diagrams none` | Show diagram source as text |
| `--overwrite` | Allow replacing an existing export |
| `--project PATH` | Select the target project root |
| `--help` | Display command usage |

Detail and diagram defaults come from the task and project presentation settings,
falling back to `full` and `auto`. The format comes from `--format`, so select
`html` explicitly when using an `.html` output filename. `export` is an alias
for `render`. These examples all use the same saved task.

```bash
riff render refunds --output refunds.md
riff render refunds --format html --output refunds.html
riff render refunds --format html --detail concise --diagrams none --output summary.html
riff export refunds --format html --output refunds.html --overwrite
```

The exporter reads the task's structured records and authored explanation.
Exporting preserves their contents and existing review status. Output paths
inside the configured task-record directory or project settings are protected,
as are source files listed in task manifests.

## Options by command

All commands below accept `--project PATH` and `--help` after the command.
For `config` and `profile`, put them after the nested command, for example
`riff config show --project PATH`. Values separated by `|` are alternatives.

| Command and arguments | Additional options |
| --- | --- |
| `init` | `--host codex\|cursor\|claude\|vscode`, `--git local\|track` |
| `configure` | `--host HOST`, `--git local\|track`, `--untrack` with `--git local` |
| `update` | `--host HOST` |
| `doctor` | `--host HOST` |
| `new TASK` | `--title TEXT`, `--route small\|standard\|complex\|critical` (default `standard`), `--profile NAME`, `--detail concise\|full`, `--diagrams auto\|none` |
| `status [TASK]` | `--details`, `--json` |
| `prompt TASK` | `--action plan\|execute\|resume\|audit` (default `plan`), `--host HOST` (default `codex`) |
| `validate TASK` | `--execution` |
| `route TASK` | Required `--host HOST` |
| `plan`, `design`, `documentation` (`docs`), `architecture`, `review`, `audit`, `research` | Required quoted request **or** `--task TASK`, plus `--host HOST` (default `codex`) |
| `debug` | Required quoted symptom **or** `--task TASK`, `--host HOST`, `--command-timeout SECONDS`, `--total-timeout SECONDS` |
| `execute TASK`, `resume TASK` | `--host HOST` (default `codex`) |
| `replan TASK` | Required `--reason TEXT`, `--host HOST` (default `codex`) |
| `show TASK` | `--detail concise\|full`, `--diagrams auto\|none`, `--json` |
| `explain TASK`, `check TASK` | `--json` |
| `graph TASK` | `--output PATH`, `--overwrite`, `--json` when writing to the terminal |
| `render TASK` (`export`) | See [Render options](#render-options) |
| `diff TASK` | Required `--against PATH` |
| `checkpoint TASK` | Required `--manifest PATH` and `--expected-generation N` |
| `reconcile TASK` | Required `--manifest PATH` |
| `migrate TASK` | `--apply` |
| `config show` | `--effective`, `--task TASK`, `--json` |
| `config set KEY VALUE` | Values accept JSON or plain text |
| `profile list`, `profile show NAME` | `--json` |

`diff`, `checkpoint`, `reconcile`, `migrate`, and profile inspection already print
JSON. The parser also accepts `--json` for these operations and `config set`, but
it does not change their output. `render` accepts that flag too and still prints
a confirmation after writing the export. Use `show --json` to inspect plan data
in JSON. `debug` inherits the Codex host default and effective timeouts, which
default to 60 seconds per command and 300 seconds total. Setup commands prompt
for a host when it is omitted. `doctor` inspects all hosts by default.

## Command directory

| Command | Purpose |
| --- | --- |
| `riff init` | Install the project skill and configure the project |
| `riff configure` | Edit build/test commands, model mappings and budgets |
| `riff configure --git local` or `riff configure --git track` | Change Git visibility for an existing project without opening the wizard |
| `riff configure --git local --untrack` | Stage removal of tracked Riff files and retain local copies |
| `riff update` | Update a project's skill using the installed Riff version |
| `riff doctor` | Inspect project settings and discover installed skill files |
| `riff new TASK` | Create draft planning records for a new task |
| `riff status [TASK]` | Show recorded plan/execution status and blocker counts |
| `riff prompt TASK` | Print the agent-chat prompt for a task |
| `riff validate TASK` | Validate plan records and live bindings for v2 READY plans |
| `riff route TASK --host HOST` | Propose dispatch assignments from saved records |
| `riff show TASK` | Read the plan with its current evaluation |
| `riff explain TASK` | Explain blockers, evidence gaps, and next actions |
| `riff check TASK` | Evaluate structure, reviews, freshness, and execution eligibility |
| `riff graph TASK` | Emit the task dependency graph as Mermaid |
| `riff render TASK` or `riff export TASK` | Export Markdown or offline HTML to `--output PATH` |
| `riff diff TASK --against SNAPSHOT` | Compare a task with a prior directory or checkpoint |
| `riff checkpoint TASK` | Save state using `--manifest PATH --expected-generation N` |
| `riff reconcile TASK --manifest PATH` | Print a recovery proposal for inspection |
| `riff migrate TASK [--apply]` | Preview or apply legacy plan migration |
| `riff config show --effective [--task TASK]` | Show resolved settings and their provenance |
| `riff config set KEY VALUE` | Validate and save a supported project setting |
| `riff profile list` or `riff profile show NAME` | Inspect available workflow profiles |

Commands accept `--project /path/to/project`. Setup commands prompt for a project
when it is omitted. Task and inspection commands use the current directory.
Supported hosts are `codex`, `cursor`, `claude`, and `vscode`.
Use `riff init --git local` or `riff init --git track` to select a mode
during setup. See [Git visibility](installation.md#git-visibility) for
which paths are affected.

## Workflow commands

These commands print a prompt to paste into the agent chat open on the
target project. They use `$riff` by default. Pass `--host cursor`,
`--host claude`, or `--host vscode` to use `/riff`.

| Command | Purpose |
| --- | --- |
| `riff plan "REQUEST"` | Plan a change and stop after plan review |
| `riff design "REQUEST"` | Compare designs and recommend an approach |
| `riff documentation "REQUEST"` or `riff docs "REQUEST"` | Request documentation advice or a scoped edit |
| `riff architecture "AREA"` | Audit existing architecture and recommend improvements |
| `riff review "TARGET"` | Review a change or plan against requirements and evidence |
| `riff audit "TARGET"` | Independently audit a spec, plan, or code change |
| `riff execute TASK` | Request execution of a reviewed plan for a saved task |
| `riff resume TASK` | Resume a saved task and reconcile its state |
| `riff research "QUESTION"` | Request a bounded investigation with sources and uncertainty |
| `riff debug "SYMPTOM"` | Request bounded reproduction and diagnosis |
| `riff replan TASK --reason "CHANGE"` | Revise the plan while preserving history and invalidating stale reviews |

Use `--task TASK` in place of a quoted request to refer to an existing task,
such as `riff review --task refunds`. The execute, resume, and replan commands
take the saved task ID directly.

## Start a task

```bash
riff init --host cursor
riff new refunds --title "Partial refunds" --route critical
riff plan --task refunds --host cursor
```

`new` creates `plan.md` and a DRAFT schema-v2 `plan.json` in the configured task-record
folder. The initial route is provisional until the planning agent inspects
the task. A Git HEAD value is recorded if available. The planning agent still
needs to inspect uncommitted changes and define requirements. Task creation
refuses to overwrite an existing task. IDs may contain letters, digits,
underscores and hyphens, up to 80 characters.

Use `--profile NAME` to select a workflow profile, `--detail concise|full` for
the reading preference, and `--diagrams auto|none` for diagram presentation.
Profiles influence planning sections and verification obligations. Risk is
assessed separately using `--route` and the agent's investigation.

Paste the prompt into your agent chat to start planning. Once the plan is
reviewed, use the execution or resume command as appropriate.

```bash
riff execute refunds --host cursor
riff resume refunds --host claude
```

`riff prompt TASK --action plan|execute|resume|audit` remains available.
Execution begins when you send the execution prompt in the host.

## Inspect and validate

```bash
riff status
riff status refunds --json
riff status refunds --details --json
riff explain refunds
riff check refunds --json
riff doctor --host cursor
riff validate refunds
riff validate refunds --execution
```

Status reads saved records. Doctor checks local configuration and skill locations.
The active editor must confirm skill discovery and actual model access.
Plan validation checks structure, so a structurally valid DRAFT may pass. For a
v2 plan marked READY, it also checks live authored documents, behavioral
configuration, source fingerprints, and current review bindings. `riff check`
evaluates readiness even for a draft and explains failures and unknown evidence.
Use execution validation to check readiness and execution evidence together. It reads
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
