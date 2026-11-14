#!/usr/bin/env python3
"""Install the Riff terminal utility from this checkout."""
import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile


def default_prefix():
    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
        return Path(local_app_data) / "Riff"
    return Path.home() / ".local"


def write_launcher(launcher, target):
    if os.name == "nt":
        launcher.write_text(
            '@echo off\n'
            'rem # Riff managed launcher\n'
            'setlocal DisableDelayedExpansion\n'
            'set "RIFF_CLI=%~dp0..\\lib\\riff-workflow\\distribution\\riff.py"\n'
            '"%SystemRoot%\\System32\\where.exe" py.exe >nul 2>&1\n'
            'if errorlevel 1 goto python\n'
            'py.exe -3 "%RIFF_CLI%" %*\n'
            'exit /b %errorlevel%\n'
            ':python\n'
            'python.exe "%RIFF_CLI%" %*\n'
            'exit /b %errorlevel%\n',
            encoding="ascii",
        )
        return

    launcher.write_text(
        f"#!{sys.executable}\n# Riff managed launcher\n"
        f"import sys\nsys.path.insert(0, {str(target)!r})\n"
        "from distribution.riff import cli\ncli()\n",
        encoding="utf-8",
    )
    launcher.chmod(0o755)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", type=Path, default=default_prefix())
    parser.add_argument("--print-bin-path", action="store_true",
                        help="After installing, print only the launcher directory")
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        parser.exit(1, "Riff requires Python 3.10 or newer.\n")
    prefix = args.prefix.expanduser().resolve()
    target = prefix / "lib" / "riff-workflow"
    binary = prefix / "bin" / ("riff.cmd" if os.name == "nt" else "riff")
    source = Path(__file__).resolve().parent / "distribution"
    if target.is_symlink() or binary.is_symlink():
        raise SystemExit("Resolve symlinked Riff installation paths before installing.")
    if target.exists() and not (target / ".riff-installation").is_file():
        raise SystemExit("Destination contains an unmanaged installation.")
    if binary.exists() and b"# Riff managed launcher" not in binary.read_bytes():
        raise SystemExit("Another command already uses the name riff.")
    target.parent.mkdir(parents=True, exist_ok=True)
    binary.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as temp:
        stage = Path(temp) / "new"
        shutil.copytree(source, stage / "distribution",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "tests"))
        (stage / ".riff-installation").touch()
        launcher = Path(temp) / "launcher"
        write_launcher(launcher, target)
        backup = Path(temp) / "previous"
        if target.exists():
            target.rename(backup)
        installed = False
        try:
            stage.rename(target)
            installed = True
            # Use a same-filesystem temporary file for atomic launcher replacement.
            fd, path = tempfile.mkstemp(dir=binary.parent)
            os.close(fd)
            try:
                shutil.copy2(launcher, path)
                os.replace(path, binary)
            finally:
                Path(path).unlink(missing_ok=True)
        except BaseException:
            if installed:
                shutil.rmtree(target)
            if backup.exists():
                backup.rename(target)
            raise
    bin_path = binary.parent.resolve()
    if args.print_bin_path:
        print(bin_path)
    else:
        print(f"Installed {bin_path / binary.name}")
        print(f"Add {bin_path} to PATH, then run riff init.")

if __name__ == "__main__":
    main()
