# Questions that resolve decisions

Riff uses one shared questioning discipline across its workflows. It investigates
facts first, reuses settled answers, and asks focused rounds when important user
decisions remain. A complete small request can proceed without any questions.

For a deeper interview, add this in your agent chat:

```text
$riff Plan offline invoice exports. Grill me before finalizing.
```

Use `/riff` with other supported hosts. You can also append the request to a CLI
prompt after pasting it. There is no `grill` command or configuration switch.

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

These are agent instructions, not a runtime interview engine. Prompt/packaging
tests verify delivery; bounded fresh-session trials evaluate actual question
quality without claiming that every model or host will always behave correctly.
