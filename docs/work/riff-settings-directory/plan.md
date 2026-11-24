# Rename project settings to .riff

Route: standard: the configuration location is shared by CLI commands, installed
utilities, Git visibility and export protection. Baseline:
fb3b6f11cd359982030c28ebeef586104a7c94ec; initial working tree clean.
Current status/reviews are recorded in plan.json and run.json.

## Outcome and scope
New project settings live in `.riff/`, matching the plugin name. Existing
`.engineering-workflow/` projects continue to work until the directory is manually
renamed. No directory is moved automatically and no configuration is merged.
The user's naming question is pending; keeping the leading dot is a disclosed
default assumption, preserving the existing hidden-settings convention (Q-1).
No external project installation, publication or historical evidence rewrite.

## Decisions
D-1: use `.riff/` as the canonical name; retain the hidden-directory convention.
Alternative: visible `riff/`, which may collide with an existing launcher.
Owner: user; reopen if their answer chooses a visible directory.
D-2: one canonical helper chooses the settings directory across all code paths.
Legacy-only projects stay supported for reads and writes, including init/update.
Alternatives: break existing projects, or migrate their filesystem automatically.
Preserving files without moving or merging them keeps this naming refactor bounded.
If both directories exist, fail with an actionable conflict message before writes.
Reject symlinked settings or a non-directory settings path. Owner: root; reopen
if explicit automatic migration is requested.
D-3: protect and exclude both current and legacy settings namespaces. Keep host
profile fallback filenames unchanged. Existing plan/checkpoint source fingerprints
are not rewritten: a manual directory rename requires the usual freshness review.
Owner: root; reopen if the underlying record or Git-visibility contract changes.

## Requirements and acceptance
R-1/C-1: fresh installs create `.riff/`; wizard, task creation/discovery, config
show/set, routing/doctor and installed utilities use the same selected directory.
R-2/C-2: legacy-only custom settings and host paths remain usable; both-directory
conflicts and invalid settings paths fail without modifying either configuration.
R-3/C-3: exports cannot overwrite either settings tree; Git local/track/untrack
behavior covers `.riff/` and legacy settings while preserving unrelated work.
R-4/C-4: current docs, skill guidance, fixtures and tools use `.riff/`; canonical
and bundled code match. Historical work/evidence remains byte-for-byte unchanged.

T-1 is one sequential end-to-end task owned by root, reviewed independently.
Scope: planning/riff_core/config.py and its bundle; distribution install/CLI/
commands/task_commands/git_visibility, relevant tests, current docs/skill host
references, tools/pilot_features.py and tools/verify_release.py. Inputs: this plan,
baseline revision, inspected call sites. Outputs: shared path resolution and
consistent naming with compatibility tests. No dependencies; one integration owner.

Required checks: meaningful regressions for new/legacy/conflicting settings,
export protection, root discovery and routing lookup; planning, execution,
distribution, recovery and routing suites; reference parity, skill validation,
whitespace checks; independent specification, quality and final integration review.
The baseline Windows symlink skips must remain explicit. No dependencies or
configuration commands are executed merely because they are saved in settings.

## Evidence and handoff
E-1: inspected configuration consumers, installer, Git visibility, CLI and tests
at the source baseline. E-2: user requested the directory match the Riff name.
Actual review/check findings and content hashes belong in review.json and
verification.json. Plan approval precedes implementation; the user's refactor
request authorizes implementation after review. Existing accepted evidence remains
bound to its original source baseline; integration hashes are recorded separately.
