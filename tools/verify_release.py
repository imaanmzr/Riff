"""Build archives and qualify fresh wheel, sdist, standalone and skill installs."""
import argparse
from email.parser import BytesParser
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist',
                        help='Archives, SHA256SUMS and package-verification.json destination')
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    for name in ('package-verification.json', 'SHA256SUMS'):
        (output / name).unlink(missing_ok=True)
    # Optional isolated build dependencies; no runtime dependency is added.
    build_tools = ROOT / 'build/build-tools'
    sys.path.insert(0, str(build_tools))
    sys.path.insert(0, str(ROOT))
    from setuptools.build_meta import build_sdist, build_wheel
    from distribution.version import VERSION
    package_version = re.search(r'^version = "([^"]+)"$',
                                (ROOT / 'pyproject.toml').read_text(), re.MULTILINE)[1]
    if package_version != VERSION.replace('-rc.', 'rc'):
        raise RuntimeError('Package and runtime versions disagree')
    os.chdir(ROOT)
    archive = output / build_sdist(str(output))
    # Build from the actual sdist in a fresh tree: checkout build/lib may be stale.
    with tempfile.TemporaryDirectory(prefix='riff-release-build-') as temporary:
        source = Path(temporary).resolve()
        with tarfile.open(archive) as data:
            members = data.getmembers()
            for member in members:
                target = (source / member.name).resolve()
                if not target.is_relative_to(source) or not (member.isfile() or member.isdir()):
                    raise RuntimeError('Unexpected source archive member: ' + member.name)
                if member.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data.extractfile(member).read())
            source_root = source / members[0].name.split('/')[0]
        try:
            os.chdir(source_root)
            wheel = output / build_wheel(str(output))
        finally:
            os.chdir(ROOT)
    required = [
        'distribution/version.py', 'distribution/status_view.py',
        'distribution/task_commands.py', 'distribution/LICENSE',
        'distribution/skills/riff/SKILL.md', 'distribution/skills/riff/LICENSE',
        'distribution/skills/riff/references/planning/riff_core/records.py',
        'distribution/skills/riff/references/planning/riff_core/progress.py',
        'distribution/skills/riff/references/planning/riff_core/storage.py',
        'distribution/skills/riff/references/routing/adapters.py',
    ]
    assets = ROOT / 'distribution/assets'
    for item in json.loads((assets / 'manifest.json').read_text()):
        name = 'distribution/assets/' + item['file']
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != item['sha256']:
            raise RuntimeError('Asset integrity failed: ' + name)
        required.append(name)
    with zipfile.ZipFile(wheel) as data:
        if any('__pycache__' in n.split('/') or n.endswith(('.pyc', '.pyo')) for n in data.namelist()):
            raise RuntimeError('Wheel contains cached Python bytecode')
        for name in required:
            if data.read(name) != (ROOT / name).read_bytes():
                raise RuntimeError('Wheel member differs: ' + name)
        metadata = next(n for n in data.namelist() if n.endswith('.dist-info/METADATA'))
        if BytesParser().parsebytes(data.read(metadata))['Version'] != package_version:
            raise RuntimeError('Wheel metadata version mismatch')
    with tarfile.open(archive) as data:
        members = data.getnames()
        if any('__pycache__' in n.split('/') or n.endswith(('.pyc', '.pyo')) for n in members):
            raise RuntimeError('Source archive contains cached Python bytecode')
        prefix = members[0].split('/')[0]
        for name in required + ['install_cli.py', 'LICENSE', 'CITATION.cff']:
            member = prefix + '/' + name
            if data.extractfile(member).read() != (ROOT / name).read_bytes():
                raise RuntimeError('Source archive member differs: ' + name)
    commands = []
    with tempfile.TemporaryDirectory(prefix='riff-release-') as temporary:
        folder = Path(temporary).resolve()

        def run(argv, cwd=folder, env=None):
            result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                                    text=True, encoding='utf-8', timeout=120)
            def portable(value):
                return (str(value).replace(str(sys.executable), 'python')
                        .replace(str(folder), '<temporary>').replace(str(ROOT), '<checkout>'))
            commands.append({'argv': [portable(v) for v in argv], 'exit_code': result.returncode})
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)
            return result

        for kind, package in [('wheel', wheel), ('sdist', archive)]:
            installed = folder / kind
            build_env = dict(os.environ, PYTHONPATH=str(build_tools))
            run([sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check',
                 '--no-deps', '--no-compile', '--no-build-isolation', '--target',
                 str(installed), str(package)], env=build_env)
            project = folder / (kind + '-project')
            (project / '.riff').mkdir(parents=True)
            (project / '.riff/project.json').write_text('{}')
            env = dict(os.environ, PYTHONPATH=str(installed), PYTHONDONTWRITEBYTECODE='1')
            entry = [sys.executable, '-c', 'from distribution.riff import cli; cli()']
            if run([*entry, '--version'], project, env).stdout.strip() != 'Riff ' + VERSION:
                raise RuntimeError(kind + ' CLI version mismatch')
            metadata = run([sys.executable, '-c',
                            'from importlib.metadata import version; print(version("riff-workflow"))'],
                           project, env).stdout.strip()
            if metadata != package_version:
                raise RuntimeError(kind + ' installed metadata version mismatch')
            for args in [('new', kind + '-task'), ('show', kind + '-task', '--json'),
                         ('status', kind + '-task', '--json'),
                         ('research', 'Inspect the installed workflow'),
                         ('render', kind + '-task', '--format', 'html', '--output', str(folder / (kind + '.html')))]:
                run([*entry, *args, '--project', str(project)], project, env)

        prefix = folder / 'standalone'
        run([sys.executable, str(ROOT / 'install_cli.py'), '--prefix', str(prefix)])
        cli = prefix / 'lib/riff-workflow/distribution/riff.py'
        if run([sys.executable, str(cli), '--version']).stdout.strip() != 'Riff ' + VERSION:
            raise RuntimeError('Standalone version mismatch')
        run([sys.executable, str(cli), 'new', 'standalone-task', '--project', str(project)])
        installer = prefix / 'lib/riff-workflow/distribution/install.py'
        # Separate projects prevent Cursor discovery from masking its own path.
        for host in ('codex', 'cursor', 'vscode', 'claude'):
            host_project = folder / ('host-' + host)
            host_project.mkdir()
            run([sys.executable, str(installer), str(host_project), '--host', host])
            run([sys.executable, str(cli), 'doctor', '--project', str(host_project), '--host', host])
            run([sys.executable, str(installer), str(host_project), '--host', host, '--update'])
            native = {'codex': '.agents', 'cursor': '.cursor', 'vscode': '.github', 'claude': '.claude'}[host]
            skill = host_project / native / 'skills/riff'
            manifest = json.loads((skill / '.installation.json').read_text())
            if manifest['version'] != VERSION:
                raise RuntimeError(host + ' skill manifest version mismatch')
            reference = skill / 'references/planning/validate.py'
            run([sys.executable, str(reference), str(project / 'docs/work/standalone-task/plan.json'),
                 '--project', str(project)])
        run([sys.executable, str(cli), 'status', 'standalone-task', '--details', '--project', str(project)])
        run([sys.executable, str(cli), 'render', 'standalone-task', '--format', 'html',
             '--output', str(folder / 'standalone.html'), '--project', str(project)])
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (wheel, archive)}
    evidence = {'version': VERSION, 'package_version': package_version,
                'wheel': wheel.name, 'sdist': archive.name, 'required_members': required,
                'sha256': hashes, 'commands': commands, 'status': 'passed',
                'scope': 'fresh wheel, sdist, standalone CLI and four host skill installations; no live host dispatch'}
    (output / 'package-verification.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    (output / 'SHA256SUMS').write_text(''.join(f'{value}  {name}\n' for name, value in hashes.items()), encoding='ascii')
    print('Release archives and fresh installations verified: ' + str(output))


if __name__ == '__main__':
    main()
