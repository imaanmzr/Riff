# Host adapter contracts

`adapters.py` defines an integration boundary and a deterministic `FakeAdapter`.
It does not launch agents, call a provider, reserve tokens, or write workflow state.
The fake adapter is for contract tests only. Its accepted result is explicitly
simulated and cannot satisfy execution or review gates.

## Request

Call `prepare_request(proposal, plan, run, config, host, request_id, context=None)`.
It reevaluates routing against the supplied live inputs and rejects stale proposals
or modified assignments. V2 plans require the same actual context as the router.
The request binds the source baseline, execution head, plan revision, plan/run/
configuration/host digests, proposal snapshot and assignment list. The request ID
is supplied by the coordinator; changing it never authorizes retrying an attempt.

`capability_report(host)` preserves supplied model capabilities and represents
absent usage accounting as `unknown`. Model names in a proposal establish a
request, not proof that a host used that model. Before a future real dispatch, the
coordinator must recheck the proposal, persist reservations using recovery's
expected generation, and obey authorization and execution gates.

## Result and reconciliation

`validate_result(result, request)` checks request/snapshot/content identity, the
task set, outcome status, simulation marker, requested versus actual identities,
and accounting availability. Accepted real results require actual agent/model
identities satisfying verified capabilities. The validator cannot authenticate a
host or establish the truth of reported identities. Acceptance is never evidence
of implementation, passing tests, integration, or review.

Outcomes are `accepted`, `failed`, or `unknown`. Unknown outcomes retain their
reservations until the coordinator inspects the host and workspace. Failed work
requires recorded resolution before another attempt. `reconciliation_proposal`
describes the next action and always returns `retry_allowed: false`; it does not
modify task state or replay dispatch. Actual recovery remains the coordinator's
responsibility.

The fake adapter reports `actual_model: null`, `agent_id: null`, and unavailable
token accounting with `tokens: null`. It never invents actual usage, including
zero usage. It refuses repeated request IDs and repeated task/attempt pairs,
including after an unknown outcome. A new fake adapter instance has no durable
history, so it must never be mistaken for crash-safe dispatch coordination.

## Validation

Run `python routing/tests/test_adapters.py`. Tests exercise stale snapshots,
tampered assignments, missing accounting, uncertain launch reconciliation,
strict result types, and rejection of simulated success by real execution gates.
No live provider adapters are shipped in this release.
