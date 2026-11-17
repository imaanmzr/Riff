# Structured plans and readable explanations

New plans use schema_version 2. JSON owns IDs, facts and dependencies; plan.md owns
authored reasoning and contracts. Do not maintain competing copies of the same
facts. `riff render` exports a composed view without editing either source.

## Record structure

Keep requirements as an array of stable IDs and tasks as the existing task array.
Set `outcome` to the observable result and `scope` to the boundaries. Exports
display these short structured fields before the specification. Add detail and
reasoning to the authored document.
Add these arrays of objects:

| Field | Required shape |
| --- | --- |
| requirement_details | id matching a requirement, description, acceptance_checks IDs |
| acceptance_checks | id, requirements IDs, procedure, expected |
| decisions | id, choice, alternatives, criteria, consequences, owner, reopen_if, requirements/evidence IDs; supersedes IDs and replaced_by when superseded |
| evidence | id, kind, source, classification, revision or accessed date |
| reports | id, kind (research/debug/replan), path to JSON, optional narrative path (defaults to matching .md), requirements/evidence IDs |

Evidence classification is observed, inferred, assumed or unresolved. Use dated
sources and report uncertainty honestly. Reports have their own schemas/templates;
both narrative and JSON belong in reviewed_artifacts. Referenced report contents,
identity and requirement/decision links are checked, not just their existence.

## Review bindings

The planning agent captures a source_manifest object of project-relative file
names to SHA256 hashes (null means expected absence). Include relevant source,
contracts and configuration; regenerate the inventory on resume to detect added
files. This listed manifest is not automatic repository discovery. Do not include
the plan JSON or checkpoint in their own fingerprints. The reviewed_artifacts
array lists task-relative authored files, including plan.md and linked specs.

Before review, resolve effective settings with riff_core.config.resolve. Store
behavior_config, behavior_provenance and config_digest. Store authored_digest from
riff_core.records.authored_digest(task_dir, plan). The reviewer records all of:
revision, source_revision, authored_digest, config_digest, plan_digest (from
riff_core.records.plan_digest), reviewer session, independent, verdict and evidence.
These are hashes of actual content, not labels or assertions of semantic proof.

Core helpers live in planning/riff_core in the checkout and references/planning/
riff_core in an installed skill. Add that planning directory to Python's import
path when using helpers from another working directory. Always pass actual
project and task paths. Standalone validate/gates/router accept --project.

All required live inputs must match at readiness and dispatch. Changing reviewed
prose, reports, source or behavior settings requires new evidence and review.
Presentation preferences are excluded from substantive plan hashing. Optional
generated sections use exactly these markers:

    <!-- riff:generated:tasks -->
    (exact records.generated_sections(plan)['tasks'] content)
    <!-- /riff:generated:tasks -->

The graph section uses `graph` instead of `tasks`. Duplicate/nested/malformed
markers or content not exactly generated from records is rejected. Only verified
generated blocks are excluded from authored hashes. Prefer export-only rendering.

## Compatibility

Missing schema_version (or 1) means legacy. Reads do not migrate; legacy validation
retains its prior contract and cannot establish v2 freshness. Unknown versions
fail validation/dispatch. `riff migrate TASK` previews; `--apply` backs up exact
bytes and atomically changes only plan.json under a content-checked local lock.
It preserves extensions, archives old reviews, increments revision and sets DRAFT.
Fill missing structured data without inventing evidence, rebind, review, and
reconcile old execution/checkpoint bindings. No multi-file transaction is claimed.
Before restoring a backup, compare the current file with the migration output;
do not overwrite later user edits. Retain backups until recovery is verified.

## Execution freshness

The original plan source_revision never moves merely to make validation pass.
After verified integration, a run may carry source_manifest plus
source_manifest_review with verdict, revision matching head_revision,
manifest_digest, reviewer, independent and evidence. An integrated task at that
head must have qualifying spec/quality checks/reviews (and invariants for critical
work). The validator checks this evidence before using the new manifest. Unknown
or stale advancement blocks dispatch. Reviewers inspect the actual combined tree.

Frozen required_checks are obligations, not automatically executed shell commands.
Every obligation must be mapped to recorded checks by the execution agent and
reviewer; configuration cannot silently weaken the accepted contract.
