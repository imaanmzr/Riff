# Hosts and model portability

The same workflow applies with any model that can read the instructions and use
the required project tools. Host capabilities govern parallelism, model choice,
review isolation and filesystem access. Never assume capabilities by brand name.

| Host | Project skill location | Invocation |
| --- | --- | --- |
| Codex | .agents/skills/riff | $riff |
| Cursor | .cursor/skills/riff | /riff |
| VS Code Copilot | .github/skills/riff | /riff |
| Claude Code | .claude/skills/riff | /riff |

Cursor also discovers .agents/skills and .claude/skills. Reuse an existing copy
rather than installing another for Cursor. If Codex and Claude Code both require
native copies, update them together from the same package; Cursor may discover
both. Select the intended copy and keep their versions identical.

## Host configuration
The setup wizard writes host-specific capabilities to
`PROJECT_ROOT/.riff/hosts/<host>.json` and model mappings to
`PROJECT_ROOT/.riff/routing-<host>.json`. The CLI prefers these
files and falls back to shared `host.json` and `routing.json` when they are absent.
For legacy-only projects, use the same files under `.engineering-workflow/`.
Do not mix the two settings directories or silently combine their configuration.
When calling `router.py` directly, pass the chosen files by absolute path with
`--host` and `--config`. Verify declared capabilities in the active host before
dispatch. Preserve other hosts' settings during a handoff. Store no API keys in
these files.

## Models
Select the main model through the host UI/configuration. The skill follows that
model. For delegated tasks, invoke only models the host exposes to the current
session. Record requested and actual model separately. Generic profile labels
are policy, not provider API IDs. Switching from one host to another is not an
automatic cross-provider model call. API orchestration requires separate provider
integrations; this package contains none.

## Handoff between hosts
Stop or reconcile active agents in the original host first. Save source revision,
plan/run records, checks, review findings, and recovery checkpoint in the project.
In the destination host invoke resume, inspect current files, revalidate evidence,
and record the new host capabilities. Do not run two coordinators against the
same task state concurrently. Keep artifact IDs and paths, not chat history, as
the shared source of truth. A separate model does not retroactively review code;
a new review must inspect actual artifacts and evidence.

## Other agents
An agent without skill discovery can explicitly read this SKILL.md and referenced
files. This is manual instruction loading, not verified native integration.
Claude Code repository installation is distinct from uploading a skill to Claude
web/Desktop; the latter does not automatically grant access to your local project.

Sources checked 2026-11-13:
https://cursor.com/docs/skills
https://code.claude.com/docs/en/skills
https://developers.openai.com/codex/skills
