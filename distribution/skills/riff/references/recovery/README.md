# Recovery 0.3

Ask: "Resume the task using recovery/WORKFLOW.md. Inspect saved progress before continuing."

Includes atomic local checkpoints, generation-based stale-writer rejection,
checksum verification, file fingerprints, interrupted-task detection, conservative
plan/source invalidation, preserved historical records and structured handoffs.
Uses Python's standard library; advisory locking targets Linux/Unix.

Read WORKFLOW.md for commands and manifest requirements. Resume is read-only and
returns a proposal. Review that proposal and real work before saving reconciled
state or dispatching agents. Prior authorization persists; no extra approval is
required for routine safe continuation. Missing authorization cannot be invented.

Validation: 32 regressions pass (8 planning, 12 execution, 12 recovery), plus a
CLI checkpoint -> source change -> resume scenario confirming blocked state and
no checkpoint mutation during resume. Fault injection verifies preservation of
the previous checkpoint if replacement fails. This is not a power-loss or
multi-machine durability certification.

Known boundaries: only manifest-listed files are fingerprinted; regenerate the
inventory to detect additions. Source drift blocks the whole run conservatively.
No automatic side-effect retries, distributed scheduler, or global skill install.
A current checksum proves stored-content integrity, not truth of task claims.
