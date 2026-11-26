# Readable plans and investigation workflows

Examples on this page use saved task IDs. You choose an ID with
`riff new retry-bug`, which creates `docs/riff/retry-bug/plan.md` and `plan.json`
by default. Later commands use `retry-bug` to find that folder. List existing IDs
with `riff status`. See [command syntax and task IDs](commands.md#command-syntax)
for a walkthrough and [render options](commands.md#render-options) for exports.

## Clarify before finalizing a plan

`riff plan "Add partial refunds"` prints a prompt for the host agent. After
inspecting the project, the agent checks missing intent, business rules and
important edge cases, then asks a few focused questions at a time. For example,
it may ask what happens when a refund exceeds the remaining refundable amount
or when the same request is repeated, if existing requirements do not settle it.
Questions explain the consequence and offer useful choices when appropriate.

Answers become requirements and success, boundary or failure acceptance examples
in the plan. Unanswered material questions stay blocking; independent discovery
can continue while the agent waits. Clear requests and previously answered details
do not require another interview. If you skip questions, the agent labels safe
assumptions and keeps consequential unresolved choices visible. Planning still
stops after review. The same guidance applies to saved-task planning and replan,
which reuse answers unless changed intent or evidence makes them stale.

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

`show` displays the plan. `explain` describes blockers, evidence gaps and next
actions. `check` evaluates structure, consistency, live review bindings, freshness
and execution eligibility, returning nonzero if required evidence fails or is
unknown. These checks cannot prove semantic correctness or review independence.
`status` evaluates current evidence by default and shows progress, candidate-bound
reviews, dependency waits and a next action/command. Select a task to see every
implementation task; `--details` adds full review history and gate findings. JSON
keeps the existing fields and adds the richer current projection. Stored plan/run
claims remain distinct from evaluated readiness. Status is read-only.

Generated `show`/`render` handoffs use that same current action and task state.
The authored specification retains its reviewed wording, so an old handwritten
"next action" cannot replace the generated current handoff.

A plan can still say READY after the evidence behind that status becomes stale.
`check` evaluates the current files: changes to source, authored documents, or
behavioral settings can invalidate prior reviews. Missing fingerprints leave
freshness unknown. Legacy records remain readable but lack v2 review bindings.

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

Available profiles are `feature`, `bug`, `refactor`, `migration`, `documentation`,
`architecture`, and `research`. They select planning sections and required checks.
Risk routes and review requirements are assessed separately.

Settings are applied from built-in defaults, then the selected profile, project
settings, task overrides, and explicit command options. Effective output identifies where each
value came from. Behavioral changes require replanning; presentation changes do
not. `config set` supports profile/profiles, build_command,
test_command, architecture_constraints, domain_invariants, sections,
required_checks, debug_command_timeout, debug_total_timeout, detail and diagrams.
Values accept JSON or plain text. Custom profiles are objects under `profiles`.
Existing unknown project settings are preserved. Routing budgets still use
`configure` and its existing recovery/accounting rules.

## Compare, checkpoint, and migrate

```bash
riff diff retry-bug --against docs/riff/retry-bug/snapshots/revision-1
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
The JSON result includes remaining v2 errors and concrete next steps. Optional
`--manifest source-files.json` captures current source/authored/configuration
bindings from an explicit file inventory during a legacy upgrade, including during
read-only preview. It neither invents missing requirements/reviews nor changes
the original source baseline. Reconcile existing run/checkpoint records after
review; those files are not changed by migration.
Read [Record contracts](../planning/RECORDS.md) for schema and review binding details.

## Token usage and budgets

Engineering guidance is selected by the work being done. Ambiguous requirements
and interface choices use the design guide. Behavior changes use implementation
and testing guidance. Bug investigation uses the debug guide, and reviews use
the compact review guide. A clear copy change can use focused verification
directly. Risk still determines the required review and evidence.

Testing is adaptive. Agents prefer a failing regression test for bugs and small
test-first slices when useful. When a useful automated check is impractical,
they record the reason and concrete alternative evidence. Existing project tools,
terminology and documentation conventions guide their choices. Resolved terms,
decisions and evidence stay in the existing task records where possible.

The local CLI reads files and runs Python utilities. Generating prompts,
validating records, comparing snapshots, and rendering exports use local
computation. The agent host accounts for model tokens when an agent reads those
outputs, investigates code, writes plans, or performs reviews.

Saved records may reduce repeated investigation across sessions. Writing and
reviewing them also uses context. Use the small route for a clear local change
and concise views when you need a summary. Diagram visibility and export detail
are presentation choices, while the risk route determines review requirements.

Routing uses configured token budgets and recorded usage or reservations to
propose assignments. The coordinator and host supply actual usage accounting.
The host controls provider calls and spending. Riff's local pilots recorded no
comparative token or cost measurements, so token savings remain unmeasured.
See the [routing workflow](../routing/WORKFLOW.md#dispatch-protocol) for budget
accounting and the [pilot evidence](work/riff-expansion/pilots.json) for its limits.
