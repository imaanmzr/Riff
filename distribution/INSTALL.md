# Engineering Workflow — project installation

Requires Python 3.10 or newer on Windows, Linux, or macOS.
This package supplies one repository skill for Codex, Cursor, VS Code with
GitHub Copilot, and Claude Code. It can be installed with standard Python.
Provider access is supplied by your agent environment.

## Install
From the extracted Riff directory:

    python3 riff.py init --project /absolute/path/to/your/project --host codex
    python3 riff.py init --project /absolute/path/to/your/project --host cursor
    python3 riff.py init --project /absolute/path/to/your/project --host vscode
    python3 riff.py init --project /absolute/path/to/your/project --host claude

On Windows, run `py -3 .\riff.py init --project C:\work\my-service --host vscode`
from this directory. Use `python` if the Python launcher is unavailable.
For a `riff` command available across projects, run the top-level
`install_cli.py` from the full repository checkout. See the
[Windows installation guide](../docs/installation.md#windows) for the
PowerShell commands that install the CLI and update your PATH.

Choose the host you use. It adds the skill under .agents/skills (Codex),
.cursor/skills (Cursor), .github/skills (VS Code Copilot), or .claude/skills
(Claude Code), and initializes settings under
.engineering-workflow/. Existing AGENTS.md and settings are preserved. The source
folder can be moved or deleted after installation. Include the installed skill
and shared settings in your project's version control if the team should use it;
keep secrets out of host.json and task records.

For a Git project, pick Git visibility during setup or pass `--git local`
or `--git track` to `riff init`. To switch an existing project, use
`riff configure --git local` or `riff configure --git track`. Local mode
uses Git's clone-local exclusions for the Riff skill folders, settings, and
configured task-record directory. Use a dedicated task-record directory.
To keep already tracked Riff files local, run
`riff configure --git local --untrack`. Review the staged removals before
committing. The working copies stay on disk.

## Use in your agent
Open the target project and select riff. Use $riff in Codex or /riff in
Cursor, VS Code Copilot, and Claude Code.

    $riff Design the retry interface.
    $riff Audit architecture in the installer.
    $riff Update the setup docs.
    $riff Plan <feature>. Stop after the plan passes review.
    $riff Execute the reviewed plan at docs/work/<task-id>/.
    $riff Resume the task at docs/work/<task-id>/.
    $riff Audit this plan independently.

If discovery is unavailable, explicitly ask the agent to read
.agents/skills/riff/SKILL.md. A local repository install does not
install a personal skill in ChatGPT's Skills directory. For manual loading in Cursor or Claude Code, substitute the installed host
folder. Other applications can load SKILL.md explicitly; native support is not
claimed. See references/hosts.md inside the installed skill for handoffs.

## Optional default behavior
Append this sentence to your existing AGENTS.md if desired:

For feature planning, implementation, review, and recovery, follow
`.agents/skills/riff/SKILL.md`; scale process to task risk.

The installer deliberately does not change your project's instructions.

## Configure
.engineering-workflow/project.json: build/test commands, architecture constraints,
and domain invariants. Task records default to docs/work/<task-id>/.
.engineering-workflow/routing.json: model mappings, concurrency and token budgets.
.engineering-workflow/host.json: actual host models/capabilities and available slots.

Empty model mappings intentionally dispatch nothing. Ask the agent to inspect
host capabilities before setting real model IDs. Planning can run in the current
agent without the routing utility. Do not invent independent reviews if subagents
are unavailable; required independent review remains outstanding.

## Update

    python3 riff.py update --project /absolute/path/to/your/project --host claude

Use the same --host as the original install.

Updates refuse locally modified or unmanaged skill files. Preserve/reconcile
those edits first. Existing project configuration is never overwritten. Do not
run simultaneous installers against the same project.

## Remove
Delete only .agents/skills/riff from the target project. Retain
.engineering-workflow and docs/work if you want to keep configuration/history.
Remove any optional AGENTS.md reference you added yourself.

## Validation and limitations
The installer test suite covers frontmatter, bundled references, and host
installation paths. Utilities validate records and propose routing. The
selected agent host supplies live discovery and model execution.

## Cursor compatibility and multiple hosts
Cursor also discovers .agents/skills and .claude/skills. If either copy already
exists, reuse it; the installer refuses a redundant Cursor installation. If you
need both Codex and Claude Code native paths, keep those copies updated together;
Cursor may list both. Never run two coordinators on the same task concurrently.

Models are chosen through the host or its available delegation tools. This skill
is not tied to OpenAI models and does not provide cross-provider API calls.
Use optional .engineering-workflow/hosts/<host>.json and routing-<host>.json to
keep model mappings separate. Real Cursor/Claude sessions have not been exercised
here; installer and instruction compatibility have been tested.
