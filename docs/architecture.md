# Architecture

Riff has a portable skill entry point, project installation CLI, and four
reference workflows. Project settings and task records belong to the user's
repository. This lets an agent hand off work between supported hosts by reading
the same records.

## Phases

| Phase | Responsibility | Main files |
|---|---|---|
| Planning | Discovery, research, decisions, specification, task graph, plan review | `planning/` |
| Execution | Task dispatch, implementation checks, review, integration | `execution/` |
| Recovery | Checkpoints, source fingerprints, interruption and stale evidence | `recovery/` |
| Routing | Capability profiles, task conflict selection, concurrency and budgets | `routing/` |

The installable skill bundles these references under
`distribution/skills/engineering-workflow/`. `distribution/install.py` installs
it into a host's repository skill directory. `distribution/riff.py` provides the
interactive CLI. The phase utilities perform structural checks and routing
proposals. They do not start agents, authenticate to providers, or certify
semantic correctness.

## Persistent state

The plan records requirements, decisions, and task dependencies. Execution
records actual agents, checks, reviews, and integrated revisions. Recovery stores
checksummed, generation-numbered checkpoints and compares a listed file manifest
when resuming. Routing uses capability mappings and resource budgets configured
for the active host.

A new host should inspect the repository and saved state before continuing. A
checkpoint is evidence about prior work, not proof that the working tree still
matches it. Source changes can stale reviews and verification.

## Boundaries

- Agent Skills discovery differs across hosts. The package includes host-specific
  install paths and invocation guidance.
- The host controls model availability, agent parallelism, isolation, and actual
  usage accounting.
- The router cannot invoke a provider or enforce billing limits.
- Recovery fingerprints only paths in its manifest. Regenerate the manifest to
  include new files.
- The current tooling is local. It has no shared database or multi-machine lock.
- No real feature benchmark has established improved quality or lower cost.
