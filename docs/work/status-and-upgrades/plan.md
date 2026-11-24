# Reliable upgrades and current workflow status

Route: standard. These changes affect installation integrity, explicit migration
and read-only inspection contracts. Baseline: 31a9da52895babae6620622d7f827b97f72b7350;
working tree initially clean. During discovery another chat added status work in
distribution/commands.py, distribution/riff.py, distribution/status_view.py and
distribution/tests/test_status.py. These existing edits are captured as inputs.
The user clarified that this chat owns the changes. Preserve useful behavior and
tests, adapting the presentation layer to the shared projection rather than
creating competing summaries. Current execution/review state belongs in the JSON
records. User authorized these fixes and richer status output in this chat.

## Behavior
R-1: doctor inventories discoverable Riff copies, shows versions and integrity,
and reports conflicting bundles instead of a healthy result. Cursor discovery
includes .cursor, .agents and .claude. Updating Cursor targets its direct copy
when present; ambiguous shared copies require an explicit native host. Other
copies and user settings are preserved.
R-2: managed text files whose only differences are LF/CRLF remain updateable.
Actual text edits, added/missing files, symlinks, invalid manifests and binary
changes remain protected. Inspect old native-path manifest keys portably.
R-3: migration previews/applies explain missing v2 facts and the review/recovery
steps remaining. Optional --manifest binds explicit source paths and current
authored/configuration fingerprints for a legacy upgrade. It never invents
requirements/reviews, changes the original source baseline, grants READY,
modifies run/checkpoint records, or writes during preview. Existing JSON output,
backup, CAS and atomic replacement contracts remain.
R-4: status evaluates live readiness by default while retaining its existing JSON
array and task/plan_status/execution_status/blockers keys. Show title, route,
schema/revision, recorded/evaluated state, execution authorization, task counts,
current review results and blockers, dependency waits and next action/command.
Selected-task output lists task outcomes and candidate-bound reviews; --details
adds findings/evidence. All-plan output stays compact. Malformed records are
isolated rather than hiding healthy plans.
R-5: a single derived progress model supplies status, explain, show and rendered
handoffs. It uses plan/run data and existing gates, never stale authored next-action
prose. Old reviews stay history, absent reviews stay missing, unresolved readiness
prevents suggested dispatch, and a complete claim without final evidence remains
unverified. Authored specifications and their review hashes are not rewritten.
R-6: current docs, skill guidance, bundled references, changelog and regression
coverage agree. New plans remain schema 2. Orkestra is not modified or upgraded.

## Decisions
D-1: use one read-only progress projection shared by inspection/export paths.
Alternative: independent status rendering or automatically rewriting plan.md.
Shared projection avoids drift without invalidating reviewed authored documents.
D-2: normalize only CRLF/LF variants of known UTF-8 text during managed-install
comparison; binary assets and substantive content retain strict byte integrity.
Alternative: raw-only hashes, which falsely classify checkouts as edited, or broad
whitespace normalization, which could conceal edits. Never delete duplicate copies.
D-3: keep explicit migration and add guidance plus optional manifest binding.
Alternative: silently migrate on status. Preview/read commands stay read-only;
new evidence still requires real review and execution reconciliation.
Owners: root. Reopen these decisions if tests expose an unsafe ambiguity or the
user changes the desired interaction. No product decision is currently blocking.

## Delivery and checks
T-1: installation inventory, doctor/update selection and text-integrity fix.
T-2: explicit migration assistance and optional manifest bindings.
T-3: shared progress/status/handoff views and integrated documentation.
T-3 includes the existing status_view.py and test_status.py; retain a compatible
presentation adapter while sharing the pure projection with generated handoffs.
One root owner, sequential edits; no dependency requires dispatching an unreviewed
task. Integration order T-1, T-2, T-3. Independent reviewer for plan, specification,
quality and final integration. Review and integrate the combined candidate.

C-1 (R-1/R-2): isolated conflicting/equivalent copies, direct Cursor update,
ambiguous discovery, LF/CRLF-only acceptance, binary/text edits and extra/missing
files. Confirm settings/other copies survive and doctor fails on conflicts.
C-2 (R-3): preview is byte-preserving, apply backs up and archives reviews, optional
source inventory gets real fingerprints, invalid/self-referential paths cannot
write, missing facts remain visible, existing run/checkpoint bytes stay untouched.
C-3 (R-4/R-5): no-run, draft, legacy, running/rework, review, dependency wait,
integrated and complete cases; stale review revisions; invalid records; JSON
compatibility; current next action beats stale prose in exports; read-only checks.
C-4 (R-6): all five regression suite directories, bundled parity, skill validation,
whitespace and isolated installed behavior. Preserve historical work records.

The existing offline browser timeout is a documented baseline failure from the
previous task, at the same unchanged source tree. Do not count it as passed.
Use the previously reproduced exception and unchanged renderer proof if still
unrelated; keep Windows real-symlink skips explicit. Record actual commands,
candidate hashes, results, findings and limitations in verification/review records.
