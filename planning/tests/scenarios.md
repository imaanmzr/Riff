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

Use a real interface decision in an isolated checkout. Have one session
capture the rationale and acceptance criteria in the plan and obtain the
review required by the route. With execution authorized, give a fresh session
the reviewed plan and repository. Check that it finds the rationale, delivers
the first demonstrable slice, and traces verification to the requirement.
Record host, outcome, and outstanding live checks.
