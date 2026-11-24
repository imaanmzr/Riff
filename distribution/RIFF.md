# Riff distribution

This directory contains the CLI, installable skill, and offline rendering assets.
Python 3.10 or newer is required. See [INSTALL.md](INSTALL.md) for project setup,
configuration, updates, and removal.

## Run the CLI

From this directory:

```bash
python3 riff.py --help
python3 riff.py init --project /path/to/project --host codex
```

The `riff` launcher also works on Linux and macOS when executable permissions
are preserved. Keep this directory's contents together; the CLI loads its
bundled skill and assets by relative path.

## Use a project skill

After installation, open the target project in your agent host. Invoke `$riff`
in Codex or `/riff` in Cursor, VS Code Copilot, or Claude Code.

```text
$riff Plan a fix for duplicate retries. Stop after plan review.
$riff Execute the reviewed plan at docs/work/retry-fix/.
```

The host supplies model access and agent tools. Terminal workflow commands print
prompts to paste into the agent chat. Project settings, plans, and execution
records stay in the target project.

## License

Riff is distributed under the [MIT License](LICENSE). Bundled browser libraries
retain their own notices; see [asset provenance](assets/README.md).
