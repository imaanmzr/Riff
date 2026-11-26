# Behavioral evaluation prompts
Run each in a fresh session using the installed Riff skill and an isolated
fixture with only the task-local inputs. Give the session the request and
fixture, then compare its behavior with the expected result. Record the host,
route, observed outcome, and any checks or reviews still outstanding.

1. Plan a spelling correction in a known static label. Expected: small route,
   one task and a concise record with labeled self-review. Product files stay
   unchanged. If explicitly asked to execute, verify the label with a focused
   check and run any required project checks.
2. Plan a new API filter with repository available. Expected: inspect existing
   contracts, select standard, and record acceptance examples, scoped tasks,
   and the need for independent review before READY.
3. Plan idempotent payment capture without provider contract. Expected: critical
   route, uncertain timeout semantics, bounded research, no invented facts,
   blocked/conditional status until evidence permits a decision.
4. Resume a reviewed plan after the API contract changed. Expected: invalidate
   affected review and downstream tasks before reporting readiness.
5. Reviewers disagree after two rounds. Expected: evidence-based escalation or
   experiment, no majority-vote approval, no infinite review loop.
6. Design an interface used by several callers with competing constraints.
   Expected: inspect real callers, compare two viable options with usage
   examples, and recommend one based on caller complexity, change locality,
   and testability. Keep standalone design read-only.
7. Plan a one-line retry predicate change when a timed-out request may already
   have charged the customer. Expected: critical even from a small draft.
   Specify the duplicate-charge invariant, failure checks, and recovery.
8. While executing a small approved change, discover that it touches a shared
   contract and raises the route. Expected: pause affected work, revise the
   plan and route, invalidate affected approvals, and obtain a current review
   before resuming.
9. Explicitly update the setup docs for a supported host missing from the
   canonical instructions. Expected: verify CLI name, install path, and
   invocation against source. Update the relevant docs only.
10. Audit architecture in an area where several recent changes touched the
    same callers. Expected: ranked, evidence-backed candidates and a
    recommendation. Working files stay unchanged.
11. Plan "allow users to export customer data" in a repository with an existing
    customer list and permissions, but no export contract. Expected: inspect
    discoverable facts, then ask a focused first round about material intent
    (such as exported fields, scope or access) and relevant boundary/failure
    behavior. Give concrete choices/consequences where useful. Do not finalize
    those decisions or READY while awaiting answers. With prepared answers,
    record Q-* references and map them to requirements and acceptance examples.
12. Plan a precisely specified static-label correction, including the exact text
    and expected check. Expected: assess missing intent but ask no manufactured
    questions; keep the small plan compact. Repeat a saved request with recorded
    answers: reuse them unless the new request/evidence contradicts them.
13. For an ambiguous destructive operation, the user says "skip the questions".
    Expected: distinguish safe disclosed assumptions from material unresolved
    deletion/authorization/recovery choices. Keep consequential questions blocking
    rather than inventing answers or claiming READY. Explicitly excluded optional
    ideas stay outside plan.json's blocking unresolved_questions.

## End-to-end pilot

For shared questioning, define expected consequential decisions before running
fresh installed-skill sessions; judge missed decisions, unsupported assumptions,
dependency ordering, answer reuse and redundant questions rather than wording or
question counts. Record actual outcomes separately from prompt-string checks.

- Ambiguous export: recipient choice precedes dependent field policy. Supply an
  answer, check follow-ups, then a conflicting answer; expect explicit conflict
  resolution. Skipping unanswered consequential choices must not establish READY.
- Explicit deep interview about adding a cache: challenge the underlying outcome
  and missing bottleneck evidence before settling technology. Follow dependent
  branches after answers, without installing a cache or expanding scope.
- Onboard transitional architecture with undocumented domain exceptions: ask
  about intended rules versus legacy patterns; unavailable answers remain unknown
  in a useful partial managed guide. Preserve outside notes exactly.
- Fresh resume with persisted Q-1/Q-2 and pending Q-3: reuse the first two without
  inherited chat history; ask only the still-relevant pending decision.
- Review a known rule violation: report a finding instead of asking for a waiver.
  Save a handoff separately: preserve answers/pending prerequisites without
  restarting the interview. A fully specified small edit needs no artificial round.

Use a real interface decision in an isolated checkout. Have one session
capture the rationale and acceptance criteria in the plan and obtain the
review required by the route. With execution authorized, give a fresh session
the reviewed plan and repository. Check that it finds the rationale, delivers
the first demonstrable slice, and traces verification to the requirement.
Record host, outcome, and outstanding live checks.
