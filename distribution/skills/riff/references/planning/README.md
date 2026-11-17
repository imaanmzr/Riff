# Planning workflow 0.1

This project-local workflow is usable through the root AGENTS.md. It is not an
installed personal skill. Personal skill installation was blocked by a read-only
installation location and unavailable network connection.

Ask: "Use planning/WORKFLOW.md to plan <feature>. Stop after plan review."
For another repository, reference this workflow by absolute path and use that
repository's instructions and real source as context. Copy project.json only
when configuration helps; fill unknown commands from repository evidence.

Use plan.md for human-readable records; plan.json is a structural example, not
a finished plan. Replace example values. Reviews start empty: only record a
review that actually happened. validate.py checks structure, not truth.

Implemented: risk routing; evidence and decisions; specification audit;
dependency-aware assignments; capability profiles; independent review rules;
revision-bound readiness; bounded escalation; planning-only handoff.

Validation: eight structural regression tests passed. One independent behavioral
trial correctly classified payment capture with unknown provider semantics as
critical/BLOCKED and did not claim exactly-once guarantees. Other scenarios in
tests/scenarios.md remain future evaluation coverage.

Next: install as a personal skill when installation access is restored, then
pilot against a real repository. Product implementation remains outside 0.1.
