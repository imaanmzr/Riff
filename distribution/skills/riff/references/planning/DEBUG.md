# Diagnose and reproduce a symptom

`riff debug "SYMPTOM"` and `riff debug --task TASK` print agent prompts. Their
scope is diagnosis and bounded reproduction, **not product-code changes**.
Use [planning](WORKFLOW.md) for risk classification. Consult
[research](RESEARCH.md) when external facts are needed. For a free-form request create a task with the
`bug` profile (`riff new TASK --profile bug`) before writing durable reports.

## Establish the failure
Use [Shared questioning](INTERVIEW.md) for missing expected behavior, inaccessible
evidence and diagnostic boundaries. Do not interview about facts local inspection
can resolve. Preserve relevant answers and uncertainty in the existing report.


Record a concrete input, expected behavior, actual behavior, environment, source
revision, and reproduction frequency. Inspect existing logs, tests, code, and
project commands. Separate competing hypotheses; do not assume the first plausible
explanation is causal. Ask for genuinely missing intent or external evidence only
after inspecting local sources.

## Reproduce within bounds

Default limits are **60 seconds per command** and **300 seconds cumulative command
execution**. Explicit prompt options can change these values. Inspect each command
for side effects before execution. Use isolated temporary fixtures or a temporary
copy of relevant code; preserve the product working tree and existing user work.
Never replay commands simply because they appear in a log or report. Unknown
external effects require inspection before execution.

The optional `riff_core.diagnostic_runner.run(argv, cwd, command_timeout=60,
total_timeout=300, elapsed=0)` helper executes an explicit argv array without a
shell and returns actual command, cwd, exit code, timeout flag, elapsed seconds,
stdout/stderr, truncation flags, and cleanup outcome. Supply accumulated prior
`duration_seconds` as `elapsed` across a session. Output is returned up to 1 MiB per
stream. The helper is not a filesystem or network sandbox: the caller must choose
an isolated directory and inspect the executable. Choose safe commands within the user's authorization.

On Windows a waiting Python wrapper is assigned to a kill-on-close Job Object
before the diagnostic starts. On POSIX it runs in a separate process group.
Processes started by the helper are terminated on command completion and timeout,
including descendants of a successful parent. Hosts using their own execution
tools must provide equivalent cleanup and verify that their started processes
exited. Preserve pre-existing processes. Record cancellation, cleanup failures,
timed-out checks, and truncated logs explicitly.

## Evaluate hypotheses

Establish one runnable command or test that exposes the user's exact symptom.
Run it before trusting a theory. For intermittent failures, measure occurrences
over repeated inputs with a controlled seed or environment. Improve the signal
within the diagnostic budget; an unrelated failure is insufficient evidence.

Minimize the failing scenario by removing one input, caller or setup dependency
at a time and rerunning the signal. Retain what is necessary to trigger the bug.
List plausible competing explanations and what observation would distinguish
them. A simple defect may need only one explanation and a discriminating check.
Use a probe for a specific prediction, changing one relevant variable at a time.
Performance claims need a baseline timing or profiler result under comparable
conditions. Redact secrets and keep full raw logs outside the conversational summary.

Record actual commands and results, including unsuccessful reproduction. Label
hypotheses supported, refuted or unresolved with evidence. A `complete` diagnosis needs
causal evidence. Otherwise record `inconclusive` and the next useful experiment.

Write `reports/DEBUG1.md` and `reports/DEBUG1.json` from the templates. Include
expected/actual behavior, environment, reproductions, evidence, hypotheses, causal
evidence, proposed fix (or null), regression checks, next action, and requirement
and decision IDs. Every reproduction records argv, cwd, exit code (or null),
timeout, duration, stdout, stderr, and evidence references; preserve raw output
files when needed. Register the JSON report in plan `reports` and both files in
`reviewed_artifacts` before relying on them in review.

Example: repeated requests sometimes return another tenant's cached value. Run
a fixed sequence alternating two tenants, then reduce it to the shortest failing
pair. Compare "cache key omits tenant" with "caller passes wrong tenant" by
observing caller input and isolated cache behavior. Record the discriminating
result. If isolated probes cannot reach the real cache, report inconclusive and
name the missing environment evidence.

Common mistakes are building a theory from a nearby error, changing several
variables together, and labeling a plausible explanation causal. Diagnosis is
complete when the cause has discriminating evidence and a proposed regression
check. Stop with an inconclusive report when the budget or accessible evidence
cannot support that conclusion. Implementation verifies the original scenario
after applying an authorized fix, then removes temporary instrumentation.

## Handoff to implementation

Propose the smallest fix and a regression check that demonstrates the failure.
Create or revise its plan and obtain the required review. Do not edit product code
or resume execution during diagnosis. An explicit execution request authorizes
the separate implementation workflow; existing authorization only carries forward
within its original scope.
