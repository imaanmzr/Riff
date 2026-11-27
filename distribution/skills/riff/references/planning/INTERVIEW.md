# Shared questioning and elicitation

Use this discipline across Riff actions, including direct skill requests. Apply
the requested operation's scope and authorization first. This guide changes how
decisions are clarified; it grants no implementation authority or readiness.

## Discover the decisions

Investigate current instructions, relevant source, configuration, project guide
and existing task answers before asking. Separate:

- Discoverable facts: investigate them yourself; use research for unavailable
  external facts. Ask the user only for genuinely inaccessible evidence.
- Consequential user decisions: ask when an answer changes outcomes, scope,
  domain semantics, acceptance checks, or consequential failure behavior.
- Routine reversible implementation choices: decide within the authorized scope
  using project conventions. Do not turn ordinary engineering work into a survey.

After discovery assess missing intent even when a request seems implementable.
When unclear, establish the outcome, concrete success examples, audience and
exclusions before settling a mechanism. Challenge a proposed solution when it
may not serve the underlying goal. Walk through relevant boundary/failure cases;
avoid a universal checklist or speculative expansion of scope.

## Work in dependent rounds

Keep a compact decision map in existing records or the conversation: question
ID, prerequisites, answer or unresolved state, and dependent decision/work.
For example, Q-2 (export fields) may depend on Q-1 (who receives the export).
This is a decision summary, not a transcript or a new machine schema.

Ask normally one to three independent questions whose prerequisites are settled.
A question depending on an answer still pending belongs in a later round.
If a prerequisite fact is being investigated, defer only downstream questions;
continue independent read-only investigation and other answerable questions.

Ground each question in a concrete scenario. Explain the consequence and offer
meaningful alternatives, allowing free-form answers. Give a recommendation when
useful, with its relevant trade-off. Use neutral wording; do not frame agreement
as the only reasonable answer or bundle dependent decisions into one choice.

Wait for answers before settling dependent decisions. After every round recompute
the map: follow newly relevant branches, prune irrelevant ones, and connect answers
to examples/checks. If answers conflict, show the contradiction and its consequence
and ask for resolution; do not silently pick the latest statement or discard an
earlier constraint. Reuse settled answers. Reopen only when changed evidence or
intent supplies a concrete reason, and explain that reason.

## Depth and stopping

Default depth is adaptive: clear requests need no manufactured questions or
question quota. Ask enough to settle material gaps, not to fill a fixed checklist.

If the user requests `riff elicit`, adds `--elicit` to an agent action, says
"grill me before finalizing", or otherwise explicitly requests a deep interview,
systematically challenge framing, alternatives, domain semantics,
relevant edge cases and consequences within the requested action. Explore the
decisions that hang off each answer rather than repeating the opening questions.
Do not broaden the task, reopen settled answers without reason, or demand an
extra blanket confirmation before delivering the requested plan/report.

Finish when material in-scope decisions are resolved or legitimately excluded or
deferred with rationale. Disclose low-impact assumptions. A skipped question,
silence or elapsed time is not an answer. A consequential unresolved in-scope
decision remains a blocker under existing gates; calling it deferred does not
make a dependent plan READY. Independent work may proceed within its own gates.

## Apply the operation's purpose

| Action | What to clarify |
| --- | --- |
| Plan/design/replan | Outcomes, scope, alternatives, semantics, acceptance examples and consequential failures. |
| Onboard | Intended versus implemented architecture, undocumented domain rules/exceptions, legacy patterns that should not be copied. |
| Debug/research | Missing expected behavior, inaccessible evidence, decision criteria and investigation boundaries. |
| Execute/resume | Only newly consequential gaps or contradictions; reuse the reviewed contract and prior answers. |
| Review/audit | Ambiguous intent; an established violation is a finding, not a request for the user to waive it. |
| Handoff | Clarify only genuinely missing handoff intent; preserve product decisions and pending questions without restarting their interview. |

Operation-specific scope wins over the common reminder. A deep interview during
planning does not authorize implementation. A handoff records an unfinished deep
interview for continuation rather than conducting it. Research/debug retain their
own report and task rules; a conversation-only interview creates no task by itself.

## Explicit elicitation and lifecycle

`riff elicit "TOPIC"` or `riff elicit --task TASK` is standalone: stop after the
scoped interview and summarize decisions, unresolved questions and next steps.
Do not implement, create a task/questionnaire automatically, or generate a whole
task plan. A free topic stays in chat; an explicit saved-task target uses its
existing clarification records and replan/review rules for actual changed intent.

`--elicit` on an existing agent action deepens questioning without replacing that
action. Ask before decisions or mutations depending on unresolved answers. After
answers, continue the requested action under its existing authority and gates;
answers alone cannot bypass missing reviews, invalidated evidence or other blockers.
Do not add a blanket confirmation step. Changing intent still follows existing
replan/review rules. The flag alone does not invalidate plans or evidence.

Optional `--focus TEXT` narrows discussion to a decision, task or subproblem within
the requested action. It is descriptive text, not a new selector or an exemption
from required checks. Re-examine relevant rationale without needlessly repeating
settled questions; explain any concrete reason for reopening an answer.
For handoff, clarify only missing handoff-specific intent and save unfinished
product elicitation for continuation. For review, established violations remain
findings. Onboard remains static, ownership-protected and able to save partial
knowledge; execute/resume preserve their authorization and readiness requirements.

The mode lasts this request, not the project or task forever. When handing off an
unfinished task-associated interview, preserve whether elicitation is pending,
its original action/topic/focus, settled answers, prerequisites and remaining
questions in existing handoff records. Fresh resume continues only that unfinished
scope under current authorization/gates. When resolved, record completion so later
requests use adaptive defaults unless explicitly enabled again. Completed interview
history and old open questions alone are not an active elicitation-mode setting.
With no task association, standalone elicitation stays in chat unless the user
separately asks to save it. There is no persistent on/off configuration or new state
schema. Existing natural-language deep-interview requests remain supported.

## Preserve answers where they belong

- Plans: keep stable Q-* references, prerequisites, answers and dependent work in
  the authored clarification section. Link R-* requirements/C-* acceptance checks.
  Keep relevant blocking questions in plan.json's unresolved_questions; existing
  readiness gates and review bindings remain unchanged. Preserve prior answers
  and explain reopened decisions. Optional excluded ideas are not blockers.
- Onboarding: record attributed answers, intended rules versus observed behavior,
  and unknowns within the guide's managed section, preserving outside notes.
  Save useful partial knowledge when answers are unavailable. If a later task
  depends on a guide unknown, bring it into that task's clarification and blockers;
  unrelated unknowns do not globally block work or create a guide readiness gate.
- Research/debug: retain relevant answers, evidence gaps and uncertainty in their
  existing reports. Do not invent evidence or passing checks from an answer.
- Handoffs: preserve settled decisions, pending prerequisites and interview scope
  (including an unfinished deep request) for continuation. Fresh sessions reuse
  those artifacts, not assumed access to an earlier conversation.
- With no existing artifact, keep the decision map in chat. Do not create a task
  or questionnaire merely to interview. Existing operation-specific durable report
  requirements still apply when that operation is actually requested.
