# Riff
An engineering workflow for research, decide, plan, review,
execute and recover. Name availability/trademark clearance has not been checked.
Invoke the installed skill as `$riff` in Codex or `/riff` in Cursor and Claude Code.

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
