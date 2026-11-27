# Review changed behavior

Use at the review stage required by [execution](WORKFLOW.md), or the plan review
stage in [planning](../planning/WORKFLOW.md). The workflows own authority,
independence and revision gates. One independent reviewer may perform both passes.
Small work may use labeled self-review under the route rules.
Use [Shared questioning](../planning/INTERVIEW.md) for ambiguous intent. An
established violation is a finding, not a question inviting the user to waive it.
`review --elicit` can clarify criteria more deeply; `--focus` does not exempt
required review coverage or turn a known violation into a waiver request.

## Procedure
Consult relevant optional project guide sections using
[Onboarding's rules](../planning/ONBOARD.md#use-during-later-work); verify against
actual instructions and source rather than treating derived claims as requirements.


1. Read the request, current specification, scoped diff or plan, and actual check
   evidence. Establish the candidate revision. Follow the changed behavior through
   callers and relevant tests. Reuse unchanged evidence by reference.
2. **Specification pass:** trace each requirement to observable behavior and a
   check. Inspect important boundaries, error paths, repeated actions and partial
   completion where relevant. Check compatibility and recovery promises. For a
   plan, verify that tasks and acceptance examples can establish those promises.
3. **Quality pass:** inspect whether interfaces fit callers, responsibilities are
   clear, and added complexity serves this change. Check test sensitivity and
   expected values. Look for internal mocking that hides the affected integration.
   Consult design or implementation guidance only for an unresolved concern.
4. Report actionable findings with severity, source location, consequence and a
   resolution check. Distinguish observed defects from questions. After a change,
   review the affected candidate and refreshed evidence before accepting it.

Example: an optional API limit is documented as positive. A test asserting only
that the response is nonempty passes when zero is accepted. Flag the missing
zero/error behavior and the insensitive assertion separately. Verify explicit
boundary assertions and the original successful request after correction.

Common mistakes are repeating the author's explanation as verification, requesting
an unrelated refactor, duplicating lint findings, and treating recorded approval
as proof that evidence is current. Examine the source behind material claims.

Complete when coverage, feasibility and relevant failure behavior are supported,
blocking findings are resolved, and the existing record contains separate spec
and quality verdicts where execution requires them. Report unavailable checks
and residual uncertainty honestly. Keep comments proportional to changed behavior.
