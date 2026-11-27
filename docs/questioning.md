# Elicitation and questions that resolve decisions

Riff uses one shared questioning discipline across its workflows. It investigates
facts first, reuses settled answers, and asks focused rounds when important user
decisions remain. A complete small request can proceed without any questions.

For standalone requirements elicitation, or deeper questioning within an action:

```bash
riff elicit "Offline invoice exports"
riff elicit --task invoice-export --focus "retry behavior"
riff plan "Add invoice exports" --elicit
riff onboard --elicit --focus "domain rules"
riff execute invoice-export --elicit --focus "retry behavior"
riff resume invoice-export --elicit
```

These commands print prompts; paste the complete prompt into your agent chat.
`elicit` requires a topic or `--task TASK`, not both, and stops after the interview
summary. A free topic stays in chat, works without Riff configuration, and creates
no task. An explicit task uses existing clarification/replan/review records.

`--elicit` is available on every agent action (including `docs` and legacy
`prompt`), not deterministic utilities such as `status`, `check` or configuration.
It deepens questioning and then continues the original action after relevant
answers, within existing authority and gates. `--focus` is optional descriptive
text; it requires `elicit` or `--elicit` and never excludes required checks.
`riff prompt TASK --action elicit` is equivalent to `riff elicit --task TASK`.
Existing `--project` and four-host `--host` options apply; Codex is the default.

Natural-language deep requests remain supported in chat:

```text
$riff Plan offline invoice exports. Grill me before finalizing.
```

Use `/riff` with other supported hosts. You can also append the request to a CLI
prompt after pasting it. There is no `grill` alias or persistent mode switch.

The agent examines goals, success examples, alternatives and relevant consequences
before committing to a mechanism. It normally asks one to three independent
questions per round. Answers reshape the next round: for example, who receives
an export may need to be settled before deciding what fields it should contain.
Recommendations include trade-offs; alternatives and free-form answers remain open.

Prior answers are reused unless intent or evidence changes. Contradictions are
made explicit. Skipping a consequential question does not resolve it or make a
dependent plan READY. Low-impact assumptions are disclosed. Legitimately excluded
ideas need not block the scoped plan. Deep questioning does not expand the task,
authorize implementation, or add a final blanket approval step.

Answers stay in existing records: plan clarification sections and linked acceptance
examples, the managed project guide, diagnostic/research reports, or task handoffs.
A standalone interview stays in chat; it creates no questionnaire or task by itself.

Onboarding can ask which existing patterns are intentional or legacy, and which
domain rules have undocumented exceptions. It may save useful partial knowledge
when answers are unavailable. Unknowns enter a later task's blocking questions
only when that task depends on them. Personal notes outside the managed section
remain untouched.

Execution and resume ask only about new consequential gaps. Review reports an
established violation as a finding. Handoff saves pending decisions without
restarting the interview. Each action retains its existing authority and gates.

Explicit elicitation lasts one request. A task handoff records pending versus
completed scope, original action/topic/focus and remaining prerequisites. Fresh
resume continues only an unfinished scope; completion restores ordinary adaptive
defaults for later requests. Actual changed intent still needs existing replan
and review handling. Enabling the flag alone does not invalidate evidence or
authorize implementation. `handoff --elicit` only clarifies missing handoff intent
and preserves unfinished product elicitation without reopening settled choices.

These are agent instructions, not a runtime interview engine. Prompt/packaging
tests verify delivery; bounded fresh-session trials evaluate actual question
quality without claiming that every model or host will always behave correctly.
