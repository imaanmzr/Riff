# Release Riff 1.0.0-rc.1

Prepare a GitHub release candidate with consistent versions, useful repository
documentation, automated checks, and verified downloadable packages. Route:
standard, because prerelease version reporting and release verification affect
installed behavior. Original baseline: commit `8eb0411`; revision 3 uses the
current content fingerprint and full source manifest recorded in plan.json.

The user requested this version and a GitHub documentation/requirements check.
Q-1: interpret “GitHub page” as the repository and its Releases page. A separate
website, PyPI upload, marketplace submission, and new host integrations are out
of scope. No unresolved product decision blocks preparation. Publication must
use an explicitly marked prerelease after qualification; failed checks remain
visible and block publishing. Do not claim unrun CI or live host certification.

## Behavior and decisions

D-1: display `1.0.0-rc.1` in the CLI, skill, citation, changelog and GitHub tag
`v1.0.0-rc.1`; package metadata uses the equivalent Python version `1.0.0rc1`.
Reuse one runtime display version for CLI and installation manifests. Doctor
must preserve the prerelease suffix rather than report stable `1.0.0`.

D-2 (superseded by D-4): the original plan used read-only CI and an authenticated
manual publishing client. That client's release authentication is unavailable.

D-4: add CI for all five unittest directories and reference parity on Windows
and Linux, at the Python minimum and a recent Python. Require a browser job with
Node 22 and Chromium, plus package verification. Branch/PR CI is read-only.
An explicit RC tag push invokes a separate release workflow that reuses the
same qualification jobs, then gives only its publishing job contents:write.
It drafts the RC, attaches qualified artifacts and publishes with prerelease
and not-latest settings. No stable-tag publication or package-index upload.
Fix a test harness defect only if evidence shows
the existing browser timeout is in the harness; do not weaken browser assertions.

D-3: add release notes, a maintainer checklist, bug/feature and PR templates,
and RC install/upgrade instructions. Keep historical version examples intact.
GitHub's community files are recommendations, not release gates. A security
contact/policy and code of conduct need an actual maintainer reporting channel;
report those as optional follow-ups rather than invent one.

## Delivery and acceptance

One integration owner `/root`; independent reviewer `/root/clarification_review`.
Implement sequentially in one checkout, preserving existing records.

- R-1 / C-1 / T-1: consistent RC identity in source, wheel, standalone CLI and
  installed skill; doctor reports the complete prerelease version. Exercise
  legacy and RC version inspection and compare built package metadata.
- R-2 / C-2 / T-2: release verification builds and checks the wheel and source
  archive, installs from both, exercises installed status/doctor/render and
  skill validation, checks asset hashes/licenses and writes checksums/evidence
  under ignored release outputs. Never overwrite historical evidence. Run all
  five suites, reference parity and the browser test without bypassing failures.
- R-3 / C-3 / T-3: README, installation, contributing and release notes explain
  how to install this exact RC, migrate safely, inspect status, and report bugs.
  Distinguish installer coverage, recorded host usage and unverified live hosts.
  CI uses read-only permissions and immutable action references; templates parse.
- R-4 / C-4 / T-4: audit GitHub metadata/releases/community files/CI, then release
  the exact reviewed commit after its remote CI passes. Verify the new immutable
  tag `v1.0.0-rc.1` targets that commit, publish with prerelease=true and without
  a latest-stable designation, attach the qualified wheel/sdist/checksums, and
  download the assets to verify hashes and final release URL/state. Preserve
  existing tags/releases; a conflicting tag is a blocker, never force-updated.
  If authentication or CI prevents publication, leave T-4 incomplete and report
  the concrete remaining step. No remote source edits outside release scope.

Inputs are this plan and the recorded source baseline. T-2 depends on T-1;
T-3 depends on T-2; T-4 depends on T-3 and final independent candidate review.
T-4 is owned by `/root`, uses coding/release capability, and outputs the verified
GitHub prerelease and downloadable assets. Scope: version-bearing source/docs, installer inspection,
distribution tests, release tooling, `.github/`, and browser test harness only
if the bounded investigation supports D-2. Outputs: RC packages/checksums,
updated docs/CI/templates, and verification/review records. Capability: coding.

## Evidence and limits

- E-1: local metadata still `0.8.0`; installer version regex truncates RC suffix;
  package verifier writes a historical task's evidence and never installs sdist.
- E-2: public GitHub API inspected 2026-11-24: MIT/README/CONTRIBUTING present;
  no releases, workflows, issue/PR templates or topics; homepage unset.
- E-3: GitHub release and community profile documentation, and PyPA version
  specifiers, accessed 2026-11-24. Links in the release checklist.
- E-4: previous task verification explicitly records the browser timeout;
  qualification must reproduce and diagnose it, not reclassify it as a pass.

Rollback: revert release preparation changes before publication; do not retag an
already public candidate. No task schema/configuration migration is introduced.
Review spec compliance and code quality separately, then review the exact final
candidate and evidence. Stop all processes started for checks before handoff.
