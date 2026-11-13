#!/usr/bin/env python3
"""Run the Riff project installer from the repository root."""
from distribution.riff import main

if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, EOFError, KeyboardInterrupt) as exc:
        raise SystemExit("Stopped: " + str(exc))
