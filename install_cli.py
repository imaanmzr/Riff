#!/usr/bin/env python3
"""Install the Riff terminal utility from this checkout."""
import argparse
from pathlib import Path
import shutil
import sys
import tempfile
import os

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", type=Path, default=Path.home() / ".local")
    args = parser.parse_args()
    prefix = args.prefix.expanduser().resolve()
    target = prefix / "lib" / "riff-workflow"
    binary = prefix / "bin" / "riff"
    source = Path(__file__).resolve().parent / "distribution"
    if target.is_symlink() or binary.is_symlink():
        raise SystemExit("Resolve symlinked Riff installation paths before installing.")
    if target.exists() and not (target / ".riff-installation").is_file():
        raise SystemExit("Destination contains an unmanaged installation.")
    if binary.exists() and "# Riff managed launcher" not in binary.read_text():
        raise SystemExit("Another command already uses the name riff.")
    target.parent.mkdir(parents=True, exist_ok=True)
    binary.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as temp:
        stage = Path(temp) / "new"
        shutil.copytree(source, stage / "distribution",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "tests"))
        (stage / ".riff-installation").touch()
        launcher = Path(temp) / "launcher"
        launcher.write_text(
            f"#!{sys.executable}\n# Riff managed launcher\n"
            f"import sys\nsys.path.insert(0, {str(target)!r})\n"
            "from distribution.riff import cli\ncli()\n"
        )
        launcher.chmod(0o755)
        backup = Path(temp) / "previous"
        if target.exists():
            target.rename(backup)
        try:
            stage.rename(target)
            # Use a same-filesystem temporary file for atomic launcher replacement.
            fd, path = tempfile.mkstemp(dir=binary.parent)
            os.close(fd)
            try:
                shutil.copy2(launcher, path)
                os.replace(path, binary)
            finally:
                Path(path).unlink(missing_ok=True)
        except BaseException:
            shutil.rmtree(target)
            if backup.exists():
                backup.rename(target)
            raise
    print(f"Installed {binary}")
    print(f"Add {binary.parent} to PATH, then run riff init.")

if __name__ == "__main__":
    main()
