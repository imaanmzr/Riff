# Releasing Riff

The current candidate is `1.0.0-rc.1`, tagged `v1.0.0-rc.1`; Python distribution
metadata normalizes it to `1.0.0rc1`. A GitHub prerelease is separate from stable
1.0.0 and from a package-index or plugin-marketplace submission.

## Prepare and qualify

1. Align `distribution/version.py`, `pyproject.toml`, skill `SKILL.md`, CLI/docs,
   `CITATION.cff`, changelog and release notes. Preserve historical examples.
2. Run the five unittest discovery commands in [CONTRIBUTING](../CONTRIBUTING.md),
   plus `python tools/sync_references.py --check` and `git diff --check`.
   Provide Node 22+ and `RIFF_BROWSER` for the Chromium offline/security test;
   a skipped or failed browser test does not qualify a release.
3. Install build-only dependencies in an isolated environment or
   `build/build-tools`: `python -m pip install --target build/build-tools
   "setuptools>=68" wheel`. Riff's runtime remains standard-library only.
4. Run `python tools/verify_release.py --output-dir dist/release`. It verifies
   archive members, absence of cached bytecode, asset hashes/licenses, normalized metadata, fresh wheel and
   sdist installation, standalone CLI and all four host skill paths. Inspect
   `package-verification.json` and `SHA256SUMS` in that directory. The wheel is
   built from a fresh extraction of that source archive to avoid stale build files.
5. Review the exact candidate and evidence, commit the reviewed changes, and
   push the release commit. Require the entire GitHub CI workflow to pass for
   that commit. Download the `release-packages` artifact from that run to use
   its qualified wheel, sdist, checksums and package verification evidence.
   Do not publish artifacts from a different source revision.

Branch/PR CI uses read-only permissions and pinned action commits. It exercises Windows
and Linux on Python 3.10/3.13; it does not certify live agent-host sessions.
Record actual checks and support limits in the release notes.

## Publish the GitHub prerelease

The normal path is the [Release candidate workflow](../.github/workflows/release.yml).
After the reviewed commit passes branch CI, push its annotated RC tag only. Do
not create a GitHub release in the web UI first; the workflow owns release
creation and uploads the qualified packages. That tag push reuses all
qualification jobs, then grants only the publishing job `contents: write`. The job
validates the tag/version/commit and artifacts, creates a draft, uploads its
qualified packages, publishes a prerelease with `latest=false`, and downloads
the assets to verify their hashes. No personal access token or package-index
credentials are required.

The workflow handles `v*-rc.*` tags only and refuses a published release or any
release that already has assets. It can resume an empty draft that targets the
same commit. If you created a release manually, delete that release (keep the
tag) and re-run the failed publish job. If a failure leaves a draft, inspect its
artifacts and qualification evidence before finishing that draft manually; do not
overwrite the tag or an existing release with assets.
The following steps also describe that manual path.

Use the [GitHub release form](https://github.com/imaanmzr/Riff/releases/new) or
GitHub CLI with an authenticated account that can write to the repository.

1. Verify no existing tag/release conflicts with the candidate. Create an
   annotated `v1.0.0-rc.1` tag pointing to the exact reviewed CI-qualified commit,
   then push that tag. Never replace an already published candidate tag.
2. Draft a release titled `Riff 1.0.0-rc.1` using
   [the release notes](releases/1.0.0-rc.1.md). Mark **This is a pre-release**;
   do not designate it as the latest stable release.
3. Attach the wheel, `.tar.gz` source distribution, `SHA256SUMS` and
   `package-verification.json` from the qualified run. GitHub's automatic source
   ZIP/tar archives do not replace the install-tested distribution assets.
4. Inspect the draft, then publish. Download the attached packages and verify
   their hashes against `SHA256SUMS`. Check the tag target, release URL, assets
   and `prerelease` state. Record those facts in the release task evidence.

GitHub recommends preparing a draft with all assets before publishing when
immutable releases are enabled. See [GitHub release management](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
and [PyPA version normalization](https://packaging.python.org/en/latest/specifications/version-specifiers/).

## Repository page

Required for this project: clear README and exact-version installation steps,
license/notices in packages, changelog/RC notes with upgrade instructions and
known limitations, passing qualification, an accurate tag and marked prerelease.
GitHub itself does not require a website, a perfect community score or PyPI
publication to create a release.

The repository includes contribution guidance, bug/feature templates and a PR
template. Additional [GitHub community recommendations](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories)
include a code of conduct and a security reporting policy. Before adding these,
choose a real maintainer contact/private reporting channel and enforcement
process. Do not publish an invented contact or claim private reporting is enabled
without checking repository settings. These are follow-ups, not RC release gates.

Keep the About description accurate. Useful optional topics are `coding-agents`,
`developer-tools`, `workflow`, `codex`, and `cursor`. A separate GitHub Pages
site is optional; the README and linked docs already provide the project guide.
