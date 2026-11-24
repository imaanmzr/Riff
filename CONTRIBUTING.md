# Contributing to Riff

Bug reports, documentation fixes, and focused pull requests are welcome.
Use [GitHub issues](https://github.com/imaanmzr/Riff/issues) to report a problem
or discuss a proposed feature.

## Report a bug

Include your operating system, Python version, `riff --version`, agent host,
the command or workflow you ran, and steps to reproduce the problem. Describe
what you expected and what happened. Include the error output and a minimal
task record when it helps, with credentials and private project details removed.

For changes to task schemas, workflow gates, or host support, describe the
intended behavior in an issue before making a large change.

## Work from source

Clone the repository and run the CLI without installing it:

```bash
git clone https://github.com/imaanmzr/Riff.git
cd Riff
python3 riff.py --help
```

Python 3.10 or newer is required. The CLI and Python regression tests use the
standard library. Packaging requires setuptools 68 or newer. The browser test
also requires Node.js 22 or newer and a Chromium-based browser.

## Check your changes

Run these suites from the repository root:

```bash
python3 -m unittest discover -s planning/tests
python3 -m unittest discover -s execution/tests
python3 -m unittest discover -s recovery/tests
python3 -m unittest discover -s routing/tests
python3 -m unittest discover -s distribution/tests
python3 tools/sync_references.py --check
```

Run both planning and execution regression suites for workflow changes. Run
recovery tests when changing workflow state or readiness rules, and routing tests
when changing dispatch, budgets, or capabilities. Add regression coverage for
behavior changes, especially stale reviews, repeated dispatch, overwritten user
settings, and task conflicts. Check installed behavior as well as source helpers.

## Edit workflow references

The canonical workflows are in `planning/`, `execution/`, `recovery/`, and
`routing/`. Edit those files first, then synchronize the copies shipped in the
skill:

```bash
python3 tools/sync_references.py
python3 tools/sync_references.py --check
```

The Python core in `planning/riff_core/` is synchronized by the same command.
Keep the MIT notices in the root, distribution, and installed skill consistent.
Preserve the separate notices accompanying third-party assets.

## Submit a pull request

Keep the change focused. Explain the problem, the resulting behavior, and how
you verified it. Update affected docs and command examples. State which checks
were skipped and why.

## Release verification

1. Run all regression suites and the reference parity check above. For browser
   verification, set `RIFF_BROWSER` to a Chromium-based browser executable and
   provide Node.js 22 or newer. Windows Chrome and Edge are detected automatically.
2. Test CLI initialization, configuration, and updates for each host. Installer
   coverage does not establish that a live host session works.
3. Verify the hashes and license notices for bundled browser assets.
4. Build the wheel and source archive with `python3 tools/verify_release.py`.
   This also exercises isolated wheel, standalone CLI, and skill installations;
   it writes archives, `SHA256SUMS` and `package-verification.json` under `dist/`.
   Use `--output-dir dist/release` for an isolated release directory. It also
   installs the source archive and verifies all four host skill paths.
5. Inspect both archives for the core utilities, rendering assets, and MIT license
   notices. Record any checks or host sessions that were not run.
6. Update the version in package metadata, the CLI, skill, and citation metadata.
   Describe the release in [CHANGELOG.md](CHANGELOG.md).

Follow [the release checklist](docs/releasing.md) before tagging or publishing.
GitHub CI runs all five directories, reference parity, browser verification and
fresh package installations. A local pass does not establish a remote CI pass.

## License

Contributions are distributed under Riff's [MIT License](LICENSE).
