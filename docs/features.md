# Readable plans and investigation workflows

## Read, explain, and export

```bash
riff new retry-bug --profile bug --detail concise --diagrams auto
riff show retry-bug
riff explain retry-bug --json
riff check retry-bug
riff status retry-bug --details --json
riff graph retry-bug --output dependencies.mmd
riff render retry-bug --format markdown --output readable-plan.md
riff export retry-bug --format html --output readable-plan.html
```

`show` reads the human view. `explain` describes blockers, evidence gaps and next
actions. `check` evaluates structure, consistency, live review bindings, freshness
and execution eligibility, returning nonzero if required evidence fails or is
unknown. These checks cannot prove semantic correctness or review independence.
`status` keeps its existing fields; `--details` adds current evaluation.

Recorded READY is distinct from evaluated readiness. A changed source file,
authored contract or behavior profile can invalidate it. Missing fingerprints
mean unknown freshness. Legacy records remain readable but lack v2 bindings.

`show` and `render` accept `--detail concise|full` and `--diagrams auto|none`.
Inspection commands accept `--json`. `graph` emits Mermaid to stdout by default;
an explicit output path writes a file. `render` (alias `export`) writes only the
requested output; it never edits plan records. Existing outputs require
`--overwrite`. Task records, project settings and listed source files are protected.
Output parent directories must already exist. Relative output paths use the
terminal working directory; task paths use `--project` or the current project.

HTML includes pinned browser libraries and works offline without npm or a server.
Raw HTML, external images, clickable links and Mermaid configuration directives
are disabled. A plain-text fallback and diagram source remain available. Diagram
rendering does not establish behavioral truth. PDF export is not included.

## Research, diagnose, and revise

```bash
riff research "Compare retry strategies" --host cursor
riff research --task retry-bug
riff debug "Retry duplicates an action" --command-timeout 30 --total-timeout 180
riff debug --task retry-bug
riff replan retry-bug --reason "The upstream API has no idempotency key"
```

These commands print prompts; the invoked host agent performs the workflow.
Research records dated sources, competing evidence and uncertainty. Debug allows
bounded isolated reproduction and diagnosis, not product edits. Defaults are 60
seconds per command and 300 total; project/task settings or explicit flags can
change them. The diagnostic helper is not a sandbox: commands must be inspected
before running. Replan preserves snapshots and decisions, increments revision,
invalidates reviews and stops before execution. See the installed workflow guides.

## Profiles and settings

```bash
riff profile list
riff profile show migration
riff config show --effective
riff config show --effective --task retry-bug
riff config set profile research
riff config set debug_command_timeout 45
```

Profiles: feature, bug, refactor, migration, documentation, architecture, research.
They select sections and suggested checks, not risk routes or review exemptions.
Settings resolve built-ins, project/profile, task overrides, then explicit options.
Effective output includes provenance. Behavioral changes require replan;
presentation changes do not. `config set` supports profile/profiles, build_command,
test_command, architecture_constraints, domain_invariants, sections,
required_checks, debug_command_timeout, debug_total_timeout, detail and diagrams.
Values accept JSON or plain text. Custom profiles are objects under `profiles`.
Existing unknown project settings are preserved. Routing budgets still use
`configure` and its existing recovery/accounting rules.

## Compare, checkpoint, and migrate

```bash
riff diff retry-bug --against docs/work/retry-bug/snapshots/revision-1
riff checkpoint retry-bug --manifest source-files.json --expected-generation 0
riff reconcile retry-bug --manifest source-files.json
riff migrate old-task
riff migrate old-task --apply
```

Diff accepts a prior task directory or checksummed checkpoint file. It reports
field changes and prose differences when both versions contain prose; checkpoint
prose is explicitly unavailable. Text comparison is not semantic equivalence.

The manifest is a JSON array of project-relative files; checkpoint state lives at
`TASK/checkpoint.json`, alongside plan.json/run.json. Pass the generation you
actually observed (0 initially). Stale writers fail without automatic retries.
Reconcile only prints a proposal and never adopts it or replays external actions.

Migration previews by default. Applying writes only plan.json, preserves exact
backup bytes and extension fields, archives reviews, increments revision and
sets DRAFT. Old execution bindings remain stale until reviewed reconciliation.
Read [Record contracts](../planning/RECORDS.md) for schema and review binding details.
