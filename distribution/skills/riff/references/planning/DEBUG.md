# Diagnose and reproduce a symptom

`riff debug "SYMPTOM"` and `riff debug --task TASK` print agent prompts. Their
scope is diagnosis and bounded reproduction, **not product-code changes**.
Use [planning](WORKFLOW.md) for risk classification and [research](RESEARCH.md)
for evidence standards. For a free-form request create a task with the
`bug` profile (`riff new TASK --profile bug`) before writing durable reports.

## Establish the failure

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
an isolated directory and inspect the executable. Do not claim it can prevent a
malicious command from changing arbitrary files or using external resources.

On Windows a waiting Python wrapper is assigned to a kill-on-close Job Object
before the diagnostic starts. On POSIX it runs in a separate process group.
Processes started by the helper are terminated on command completion and timeout,
including descendants of a successful parent. Hosts using their own execution
tools must provide equivalent cleanup and verify that their started processes
exited. Preserve pre-existing processes. Record cancellation, cleanup failures,
timed-out checks, and truncated logs explicitly.

## Evaluate hypotheses

Record actual commands and results, including unsuccessful reproduction. Change
one relevant variable at a time where practical. A matching symptom supports a
reproduction; it does not alone prove the cause. Distinguish supported, refuted,
and unresolved hypotheses, with evidence references. A `complete` diagnosis needs
causal evidence. Otherwise record `inconclusive` and the next useful experiment.

Write `reports/DEBUG1.md` and `reports/DEBUG1.json` from the templates. Include
expected/actual behavior, environment, reproductions, evidence, hypotheses, causal
evidence, proposed fix (or null), regression checks, next action, and requirement
and decision IDs. Every reproduction records argv, cwd, exit code (or null),
timeout, duration, stdout, stderr, and evidence references; preserve raw output
files when needed. Register the JSON report in plan `reports` and both files in
`reviewed_artifacts` before relying on them in review.

## Handoff to implementation

Propose the smallest fix and a regression check that demonstrates the failure.
Create or revise its plan and obtain the required review. Do not edit product code
or resume execution during diagnosis. An explicit execution request authorizes
the separate implementation workflow; existing authorization only carries forward
within its original scope.
