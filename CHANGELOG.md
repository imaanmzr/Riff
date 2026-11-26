# Changelog

## Unreleased

- Add `riff onboard` to prepare agent discovery and a reusable project guide.

- Default new task records to `docs/riff/`; preserve explicitly configured paths.

## 1.0.0-rc.1 — 2026-11-24

First release candidate for stable 1.0.0. See
[release notes](docs/releases/1.0.0-rc.1.md) for installation and compatibility.

- Show live readiness, task progress, current/historical reviews, dependency waits
  and next continuation actions in `riff status`; share current handoffs with exports.
- Detect conflicting host skill copies, target direct Cursor updates correctly,
  and accept LF/CRLF-only managed text while preserving substantive/binary edits.
- Add actionable legacy migration guidance and optional explicit source-manifest binding.
- Clarify missing product intent and important edge cases through focused planning questions.
- Use `.riff/` for new project settings while preserving legacy-only settings.

- Adopt the MIT License and include license notices in CLI and skill packages.
- Revise setup, contributor, architecture, and workflow documentation for the
  public repository; remove obsolete installation status and test counts.
- Update package links and citation metadata.
- Preserve prerelease versions in installation diagnostics.
- Add GitHub CI, issue/PR templates, and release qualification instructions.
- Verify fresh wheel, source archive, standalone CLI and four host skill
  installations; generate release checksums without replacing historical evidence.

## 0.8.0 — 2026-11-16

- Add v2 structured plans, live prose/config/source review bindings, explicit
  migration with backups and content compare-and-swap, and legacy reads.
- Add readable Markdown/offline HTML exports, Mermaid dependency graphs,
  show/explain/check, snapshot diff, checkpoint and reconciliation commands.
- Add research/debug/replan workflows, validated reports, bounded diagnostic
  process cleanup, profiles and noninteractive configuration.
- Add simulated host-adapter contracts without live dispatch, shared core parity
  checks and pinned offline rendering assets.

## 0.7.0 — 2026-11-13

- Added descriptive command help and examples.
- Added doctor, new, status, prompt, validate and route commands.
- Added CLI regressions for task creation, error exits and record preservation.

## 0.6.0 — 2026-11-13

- Added an installable terminal command through a Python package or direct user installer.
- Added VS Code GitHub Copilot project skill installation.
- Renamed the installed skill command to riff with migration for managed legacy installations.

## 0.5.1 — 2026-11-13

- Renamed the interactive installer command and package to Riff.
- Added multi-host project skill installation for Codex, Cursor, and Claude Code.
- Added host-specific capability documentation and project configuration wizard.
- Added CLI tests for initialization, configuration, and safe updates.

## 0.4.0 — 2026-11-13

- Added capability-based task routing proposals, write-scope conflict detection,
  concurrency limits, token reservations, and dispatch attempt limits.

## 0.3.0 — 2026-11-13

- Added generation-numbered checkpoints, source manifest fingerprints, and
  conservative recovery proposals for interrupted work.

## 0.2.0 — 2026-11-13

- Added execution gates, task evidence records, and integration review checks.

## 0.1.0 — 2026-11-13

- Added planning workflow, templates, and structural plan validation.
