# Riff
An engineering workflow for design, documentation, planning, execution,
review, and recovery. Invoke the installed skill as `$riff` in Codex or
`/riff` in Cursor, VS Code Copilot, and Claude Code.

Riff 0.8.0 also includes research/debug/replan workflows, profile settings,
live evidence checks, and offline HTML exports with Mermaid diagrams.
Choose a task ID when creating records, then reuse it in commands.

    ./riff new refunds --title "Partial refunds"
    ./riff plan --task refunds
    ./riff status
    ./riff render refunds --format html --output refunds.html

The ID `refunds` selects `docs/work/refunds/` by default. That folder contains
plan.md and plan.json. The `plan` command prints a prompt for your agent chat.
The `render` command writes an export to the selected output path. Open the HTML
file in your browser. Use `./riff render --help` for its options.

From this extracted directory:

    ./riff init
    ./riff configure --project /path/to/project --host cursor
    ./riff update --project /path/to/project --host claude

If archive extraction loses executable permissions, use python3 riff.py.
To invoke from anywhere, add this extracted directory to PATH. Keep the whole
package together: the CLI loads the bundled skills alongside itself.

The wizard asks project/app, build and test commands, records directory,
concurrency and dispatch budget. Model IDs and host capabilities are optional.
Defaults do not establish real host access. Budgets are estimates enforced at
dispatch, not provider billing caps. Configuration commands are never executed.
It preserves existing project instructions and settings keys. Update refuses
modified skill files. Initialization installs the skill before configuring it;
canceling configuration does not uninstall it. Run one wizard per project at a time.
No package registry publication or global shell installation has been performed.
