"""Build and inspect archives, then exercise fresh isolated installations."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    # Build-only dependencies belong in this ignored directory, not the runtime.
    sys.path.insert(0, str(ROOT / 'build/build-tools'))
    from setuptools.build_meta import build_sdist, build_wheel
    os.chdir(ROOT)
    archive = ROOT / 'dist' / build_sdist('dist')
    wheel = ROOT / 'dist' / build_wheel('dist')
    required = ['distribution/assets/mermaid.min.js', 'distribution/assets/markdown-it.min.js',
                'distribution/skills/riff/references/planning/riff_core/records.py',
                'distribution/skills/riff/references/planning/riff_core/reports.py',
                'distribution/skills/riff/references/routing/adapters.py',
                'distribution/task_commands.py']
    with zipfile.ZipFile(wheel) as data:
        assert all(name in data.namelist() for name in required)
    with tarfile.open(archive) as data:
        assert all(any(name.endswith('/' + expected) for name in data.getnames()) for expected in required)
        assert any(name.endswith('/install_cli.py') for name in data.getnames())
    commands = []
    with tempfile.TemporaryDirectory(prefix='riff-release-') as temporary:
        folder = Path(temporary)
        installed = folder / 'wheel'
        def run(argv, cwd=folder, env=None):
            result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, encoding='utf-8', timeout=60)
            def portable(value):
                return str(value).replace(str(sys.executable), 'python').replace(str(folder), '<temporary>').replace(str(ROOT), '<checkout>')
            commands.append({'argv': [portable(v) for v in argv], 'exit_code': result.returncode})
            if result.returncode: raise RuntimeError(result.stdout + result.stderr)
            return result
        run([sys.executable, '-m', 'pip', 'install', '--no-deps', '--target', str(installed), str(wheel)])
        project = folder / 'project'
        (project / '.engineering-workflow').mkdir(parents=True)
        (project / '.engineering-workflow/project.json').write_text('{}')
        env = dict(os.environ, PYTHONPATH=str(installed))
        entry = [sys.executable, '-c', 'from distribution.riff import cli; cli()']
        for args in [('new', 'wheel-task'), ('show', 'wheel-task', '--json'),
                     ('research', 'Inspect the installed workflow'),
                     ('render', 'wheel-task', '--format', 'html', '--output', str(folder / 'wheel.html'))]:
            run([*entry, *args, '--project', str(project)], project, env)
        prefix = folder / 'standalone'
        run([sys.executable, str(ROOT / 'install_cli.py'), '--prefix', str(prefix)])
        cli = prefix / 'lib/riff-workflow/distribution/riff.py'
        run([sys.executable, str(cli), 'new', 'standalone-task', '--project', str(project)])
        run([sys.executable, str(cli), 'render', 'standalone-task', '--format', 'html', '--output', str(folder / 'standalone.html'), '--project', str(project)])
        installer = prefix / 'lib/riff-workflow/distribution/install.py'
        run([sys.executable, str(installer), str(project), '--host', 'codex'])
        reference = project / '.agents/skills/riff/references/planning/validate.py'
        run([sys.executable, str(reference), str(project / 'docs/work/standalone-task/plan.json'), '--project', str(project)])
    evidence = {'wheel': wheel.name, 'sdist': archive.name, 'required_members': required,
                'sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (wheel, archive)},
                'commands': commands, 'status': 'passed', 'scope': 'isolated wheel, standalone CLI and skill utility; no live host dispatch'}
    (ROOT / 'docs/work/riff-expansion/package-verification.json').write_text(json.dumps(evidence, indent=2)+'\n', encoding='utf-8')
    print('Release archives and fresh installations verified')


if __name__ == '__main__': main()
