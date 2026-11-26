# Onboard an existing project

Use for `riff onboard` and equivalent direct Riff skill requests. Inspect the
project and write its optional project guide, not product code or a task plan.
Use static investigation by default: no project commands, dependency installs,
configuration/instruction rewrites, Git writes or native chat-history capture.
Reading local Git revision/status is allowed. Report discovered commands as
unverified unless supported by actual results and their source revision/evidence.

## Locate and protect the guide

Use `riff_core.onboarding.guide_path(PROJECT_ROOT)` from the bundled planning
references. It uses the existing settings resolver: `.riff/` or legacy-only
`.engineering-workflow/`, configured `artifacts_directory` or `docs/riff` when
absent, then `project.md`. No configuration is required. Never search multiple
guide locations or fall back after invalid/duplicate settings. Other commands'
setup requirements remain unchanged. Do not create settings or install a skill.

Start with [the template](templates/project-guide.md). Its one standalone marker
pair is exactly `<!-- riff:onboard -->` and `<!-- /riff:onboard -->` in that order.
If an existing guide is a symlink, unmarked, malformed, duplicated, or not a
regular file, leave it unchanged and report the collision for user resolution.
For a valid guide, read the whole file first. Refresh only bytes between the
markers; preserve the markers and all outside bytes exactly, including newline
style and personal notes. Before saving, verify the file still matches what you
read; on concurrent edits stop and reread rather than overwriting user work.
Do not follow symlink destinations when writing a guide.

## Investigate and summarize
After static discovery use [Shared questioning](INTERVIEW.md) to elicit important
knowledge only the owner can supply: intended versus current architecture, domain
rules and exceptions, and legacy patterns new work should avoid. Ask in dependent
rounds and distinguish attributed answers from inspected facts. Save a partial
guide when answers are unavailable, keeping relevant questions in the managed
section; block only later work whose decisions depend on those answers, through
that task's existing clarification/readiness rules. Do not create a task to interview.


1. Read applicable instructions, existing architecture/domain docs, manifests,
   formatter/linter configuration and test configuration. Link canonical sources
   instead of rewriting them. Respect existing host/project instruction authority.
2. Inspect entry points, major subsystem boundaries, representative source and
   tests. Trace important request/data flows and look for conflicting patterns.
   For a large repository begin with a broad map, deepen representative areas,
   and name uninspected areas. Do not claim exhaustive knowledge.
3. Write a concise guide (roughly 150 lines, not a hard limit) covering structure,
   architecture, conventions/rules/style, semantics/invariants, working commands
   and coverage gaps. Use relative links from the guide to supporting sources.
   Mark claims as explicit rule, observation, inference or unknown. Repeated code
   patterns alone are not rules; implemented behavior is not proof of intent.
4. Record UTC inspection time, actual Git baseline or why unavailable, and dirty
   source relevant to the observations. Distinguish discovered commands, verified
   results, and prior verification tied to its revision/evidence. Do not turn a
   README command into a passing check. No new command execution is implied.
5. On refresh preserve still-applicable attributed user constraints, rationale
   and questions from the previous guide. Recheck sources; correct/remove derived
   claims whose support changed or disappeared, or mark uncertainty explicitly.
   Preserve personal notes outside the block even when stale; flag conflicts in
   the managed section. Surface contradictory sources; ask only when unresolved
   intent materially affects a dependent decision. Unknowns need not block a
   useful partial guide. A different HEAD prompts verification, not wholesale
   invalidation of the guide.
6. Report saved location, coverage, unknowns and any collision. Saved locally
   does not mean tracked or synchronized. For skill installation use existing
   `riff init --host HOST`; for Git visibility use existing configuration options
   only when requested. Do not create a task record just for onboarding.

## Use during later work

Plan, execute, review and resume selectively consult this same guide if present,
then verify relevant claims against current instructions, configuration and code.
Missing guides do not require onboarding. During normal authorized work update
only facts directly affected by the change, using the same ownership/preservation
rules. Keep canonical docs authoritative. Changed requirements belong in the
existing replan/review process, not only the guide. It grants no authorization,
readiness or new review gate.

Exclude the mutable guide from automatically generated source inventories and
review bindings. Preserve explicit user-supplied entries and their freshness
checks; do not remove bindings to make a refresh pass. Freeze consequential
requirements in the existing task plan rather than depending on mutable prose.
