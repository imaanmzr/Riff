# Continue on another machine

Riff keeps a short `handoff.md` alongside each task's plan and execution records.
The agent updates it after meaningful decisions and task transitions, or when you
ask for a handoff. It preserves constraints, rejected approaches, unfinished work,
open questions and evidence links. It does not automatically capture every message.

## Machine A: save and transfer

From the project root, prepare a handoff:

```bash
riff handoff retry-fix --host codex
```

Paste the printed prompt into your agent chat. The agent reads earlier context
and saves `docs/riff/retry-fix/handoff.md` (or your configured task directory).
The command itself only prints a prompt; it does not save files or call a model.
Use `cursor`, `vscode`, or `claude` for another supported host.

If you want to preserve a chat export, provide a UTF-8 Markdown or text file and
ask the agent to archive it with the handoff. It copies the export unchanged into
the task's `conversations/` directory, chooses a new filename if one exists, and
adds a relative link and source label. Review exported content before committing.

Review the handoff, actual code changes, and Git tracking. If Riff was configured
to keep records local, opt into tracking with the existing command:

```bash
riff configure --git track
git status --short
git check-ignore -v docs/riff/retry-fix/handoff.md
```

Other ignore rules can still apply. Select and stage the code, task records,
handoff and optional exports you intend to transfer; inspect `git diff --cached`
before committing. Use a work-in-progress branch for unfinished code. Commit and
push that branch through your normal Git workflow. Uncommitted and untracked
files do not travel with a push. Saving locally does not mean synchronized.

## Machine B: pull and resume

Pull or clone the same branch, ensure Riff is installed and the project skill is
current (`riff update --host codex`), then run:

```bash
riff resume retry-fix --host codex
```

Paste the prompt into a fresh agent session. The agent reads the handoff, current
instructions and task records, inspects source, and follows recovery checks.
It reads relevant chat excerpts only when needed. Older tasks without a handoff
still resume normally. If context conflicts with source or the plan, the agent
reconciles it or asks about changed intent before dependent work continues.

Plan/run records govern recorded readiness and verification. A suggested next
action in a handoff can become stale; `riff status retry-fix --details` provides
the generated current action. Neither a chat export nor a handoff grants new
execution authority or makes old checks current.

## Limits

There is no background saving, native chat-history integration, automatic secret
redaction, sync service, archive restore, or automatic Git operation. Transfer
credentials and machine-specific setup through your existing setup process.
Use one active coordinator per task and Git's normal conflict resolution when
machines diverge. Riff records context; the host agent writes and interprets it.
