# Contributing

Riff is an early workflow tool. Keep instructions short, make state transitions
easy to inspect, and report what is actually automated versus what the agent or
host must do.

## Local checks

```bash
python3 planning/tests/test_validate.py
python3 execution/tests/test_gates.py
python3 recovery/tests/test_state.py
python3 routing/tests/test_router.py
python3 distribution/tests/test_install.py
```

When changing workflow behavior, update the corresponding phase instructions and
skill-bundled copy. Add regression coverage for behavior that could cause stale
reviews, unsafe redispatch, overwritten user settings, or incorrect task routing.

## Release checklist

- Update the bundled skill from the canonical phase sources.
- Run the local checks above.
- Test CLI init, configure, update, and each supported host path.
- Build and inspect the release archive.
- Describe host sessions or feature pilots that remain untested.
- Add a license before public release if reuse is intended.
