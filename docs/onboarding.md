# Understand an existing project

Run from the repository you want to understand:

```bash
riff onboard
riff onboard --project /path/to/project --host cursor
```

Paste the printed prompt into your agent chat. The CLI is read-only; the agent
investigates and writes `docs/riff/project.md`, or `project.md` at your configured
Riff records root. Codex is the default host; Cursor, VS Code Copilot and Claude
Code are also supported. You can ask the Riff skill to onboard directly.

The guide records structure, architecture, conventions, rules, code style, domain
vocabulary and working commands with relative evidence links.
[Shared questioning](questioning.md) helps distinguish intended rules from legacy
behavior; unanswered questions can remain in a useful partial guide. It distinguishes
explicit rules, observations, inferences and unknowns. Investigation is static;
commands found in configuration or docs are not claimed as verified checks.
Existing documentation is linked rather than rewritten; coverage gaps are reported.

Run `riff onboard` again to refresh. The agent rechecks evidence, preserves useful
previous context, and corrects unsupported claims. Only the section between
`<!-- riff:onboard -->` and `<!-- /riff:onboard -->` is managed. Personal notes
outside it remain byte-for-byte unchanged. Existing unmarked files, malformed
markers or symlinks remain untouched; resolve the collision before retrying.

Later Riff tasks consult relevant guide sections, verify claims against current
source and instructions, and update only directly affected facts during authorized
work. Task handoffs remain task-specific. Neither changes authorization or gates.

No task, configuration, installation, Git tracking or synchronization is created
by `onboard`. It works without Git or Riff configuration. If your agent needs the
project skill installed, use `riff init --host HOST`. To opt into Git tracking,
use existing `riff configure --git track` after setup, then review and commit
intended files normally. Explicit `--git local --untrack` includes a root guide
only when it has one valid Riff-owned section; unrelated/malformed files are
skipped. Other Git ignore rules can still apply.

The guide is portable Markdown, not model training or an exhaustive code index.
No watcher, embeddings, automatic command execution or `learn` alias is provided.
