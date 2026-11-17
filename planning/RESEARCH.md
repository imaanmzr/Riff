# Research a bounded question

`riff research "QUESTION"` and `riff research --task TASK` print prompts for the
active agent host. Printing a prompt does not conduct research or create evidence.
The agent follows this workflow after the user submits that prompt.

## Start with a decision

1. Read project instructions and the [planning workflow](WORKFLOW.md). Inspect
   existing task records and sources before asking discoverable questions.
2. State the question, decision it informs, observable success criteria,
   exclusions, available sources, and a bounded research budget. Use the highest
   applicable risk route; research does not waive independent review.
3. For a free-form request, create a task through `riff new TASK --profile research`
   before writing durable reports. Choose a stable unused task ID; never overwrite
   an existing task merely because its title looks similar. For `--task`, use that
   task and preserve its scope and prior work.

## Investigate and record

Use primary evidence where available: actual repository code and tests for local
behavior; authoritative documentation for external contracts. Record exact paths
and revisions, or URLs and access dates. Distinguish **observed**, **inferred**,
**assumed**, and **unresolved** claims. Observed claims require source references.
Record conflicting evidence and plausible alternatives, including evidence that
could reopen a recommendation. Do not label speculation as verified behavior.

Only run experiments within the user's authorization. Bound commands and resource
use, isolate fixtures, and stop processes you start. Do not install dependencies,
edit product code, publish findings externally, or call a provider solely because
research was requested. If unavailable tools prevent an answer, retain uncertainty
and name the missing fact instead of fabricating findings.

Write `reports/RESEARCH1.md` and `reports/RESEARCH1.json`, using the templates in
`templates/`. Increment the report ID for a distinct investigation. The JSON report
contains question, scope, success criteria, limits, sources, classified claims,
alternatives, counterevidence, uncertainty, conclusion, next action, and linked
requirement/decision IDs. Status is `draft`, `complete`, or `inconclusive`.

Register the JSON report in plan `reports` with its stable ID, `kind: research`,
relative `path`, requirement IDs, and plan evidence IDs. Add both narrative and
JSON paths to `reviewed_artifacts` before a review relies on them. Report-local
source IDs are local to the report; do not confuse them with plan evidence IDs.

## Finish honestly

Review the report against the initial question and evidence. A completed report
may conclude that the question is unresolved: use `inconclusive`, record an
unresolved claim, and specify the next evidence-gathering action. Apply the route's
review requirements when the result changes an implementation decision.

Return the answer, evidence, uncertainty, and report paths. Update affected
decisions through planning/replanning. Research completion alone does not make a
plan READY or authorize execution.
