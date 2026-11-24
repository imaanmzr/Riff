#!/usr/bin/env python3
"""Install/update one repository-scoped skill for Codex, Cursor or Claude Code without changing AGENTS.md."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile

if __package__:
    from .core import config as project_config
    from .version import VERSION
else:
    from core import config as project_config
    from version import VERSION

NAME = 'riff'
LEGACY_NAME = 'engineering-workflow'
HOSTS={'codex':'.agents','cursor':'.cursor','claude':'.claude','vscode':'.github'}
TEXT_SUFFIXES = {'.md', '.mdc', '.py', '.json', '.yaml', '.yml', '.toml', '.txt'}


def _text_variants(path, data):
    if path.suffix.lower() not in TEXT_SUFFIXES and path.name != 'LICENSE':
        return []
    try:
        data.decode('utf-8')
    except UnicodeDecodeError:
        return []
    if b'\0' in data:
        return []
    lf = data.replace(b'\r\n', b'\n')
    return [lf, lf.replace(b'\n', b'\r\n')]


def inspect_installation(root):
    """Inspect managed bytes without treating text newline conversion as edits."""
    root = Path(root)
    result = dict(path=str(root), version='unknown', integrity='unmanaged',
                  changed_files=[], newline_only_files=[], bundle_digest=None)
    try:
        if any(p.is_symlink() for p in (root, *root.parents)):
            raise ValueError('Symlinked installation path')
        files = [p for p in root.rglob('*') if '__pycache__' not in p.parts]
        if any(p.is_symlink() for p in files):
            raise ValueError('Symlink inside installed skill')
        data = {p.relative_to(root).as_posix(): p.read_bytes() for p in files
                if p.is_file() and p != root / '.installation.json'}
        skill = data.get('SKILL.md', b'').decode('utf-8')
        version = re.search(r'^Version\s+([0-9]+(?:\.[0-9]+)+(?:-[A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*)?)', skill, re.MULTILINE)
        if version:
            result['version'] = version[1]
        canonical = {name: hashlib.sha256((_text_variants(Path(name), value) or [value])[0]).hexdigest()
                     for name, value in data.items()}
        result['bundle_digest'] = hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()
        metadata = root / '.installation.json'
        if not metadata.is_file():
            return result
        manifest = json.loads(metadata.read_text(encoding='utf-8'))
        expected = manifest.get('hashes')
        if not isinstance(expected, dict) or not expected:
            raise ValueError('Invalid installation hash manifest')
        normalized = {}
        for name, value in expected.items():
            if not isinstance(name, str) or not isinstance(value, str) or not re.fullmatch(r'[a-f0-9]{64}', value):
                raise ValueError('Invalid installation hash entry')
            name = name.replace('\\', '/')
            if name in normalized:
                raise ValueError('Duplicate installation hash path')
            # Validate legacy Windows separators without permitting traversal.
            if name.startswith('/') or ':' in name or any(p in ('', '.', '..') for p in name.split('/')):
                raise ValueError('Invalid installation hash path')
            normalized[name] = value
        changed = sorted(set(data) ^ set(normalized))
        newline_only = []
        for name in data.keys() & normalized.keys():
            value = data[name]
            if hashlib.sha256(value).hexdigest() == normalized[name]:
                continue
            variants = _text_variants(Path(name), value)
            if any(hashlib.sha256(v).hexdigest() == normalized[name] for v in variants):
                newline_only.append(name)
            else:
                changed.append(name)
        result.update(installed_version=manifest.get('version'), changed_files=sorted(changed),
                      newline_only_files=sorted(newline_only),
                      integrity='modified' if changed else 'newline-only' if newline_only else 'unchanged')
    except (OSError, ValueError, UnicodeError, TypeError, AttributeError) as exc:
        result.update(integrity='invalid', error=str(exc))
    return result


def installations(project, host=None):
    hosts = [host] if host else list(HOSTS)
    if host == 'cursor':
        hosts += ['codex', 'claude']
    found = []
    for native in dict.fromkeys(hosts):
        for name in (NAME, LEGACY_NAME):
            path = Path(project) / HOSTS[native] / 'skills' / name
            if path.exists() or path.is_symlink():
                found.append(dict(inspect_installation(path), host=native, name=name))
    return found


def installation_host(project, host):
    """Cursor updates its direct copy first; shared-copy choices are explicit."""
    if host != 'cursor':
        return host
    candidates = installations(project, host)
    if any(item['host'] == 'cursor' for item in candidates):
        return 'cursor'
    native = list(dict.fromkeys(item['host'] for item in candidates))
    if len(native) > 1:
        raise ValueError('Cursor discovers multiple shared Riff copies. Choose --host codex or --host claude explicitly; keep their bundles in sync.')
    return native[0] if native else host

def hashes(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and p != root / '.installation.json' and '__pycache__' not in p.parts}

def install(project, update=False, host="codex"):
    if host not in HOSTS: raise ValueError("Unsupported host")
    project=Path(project).expanduser().resolve()
    if not project.is_dir(): raise ValueError('Project directory does not exist')
    direct_exists = any((project / HOSTS[host] / 'skills' / name).exists() for name in (NAME, LEGACY_NAME))
    if host == 'cursor' and not direct_exists:
        for other in ('.agents', '.claude'):
            for name in (NAME, LEGACY_NAME):
                existing = project / other / 'skills' / name
                if (existing / 'SKILL.md').is_file():
                    native_host = 'codex' if other == '.agents' else 'claude'
                    raise ValueError(f'Cursor can already discover {existing}. Update it using --host {native_host}.')
    settings=project_config.settings_directory(project)
    parent=project/HOSTS[host]/'skills'
    legacy = parent / LEGACY_NAME
    for p in (project / HOSTS[host], parent, parent / NAME, legacy):
        if p.is_symlink(): raise ValueError('Refusing symlinked install path: '+str(p))
    destination=parent/NAME
    source=Path(__file__).resolve().parent/'skills'/NAME
    if destination.exists() and legacy.exists():
        raise ValueError('Both riff and engineering-workflow exist. Resolve the duplicate before updating.')
    installed = legacy if legacy.exists() else destination
    if installed.exists():
        if not update:
            raise ValueError('Already installed. Run the update command to upgrade it.')
        inspection = inspect_installation(installed)
        if inspection['integrity'] not in ('unchanged', 'newline-only'):
            raise ValueError('Installed files changed or are unmanaged. Preserve your edits before updating.')
    parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=parent,prefix='.engineering-stage-') as temp:
        stage=Path(temp)/NAME
        shutil.copytree(source,stage)
        (stage/'.installation.json').write_text(json.dumps({'version':VERSION,'host':host,'hashes':hashes(stage)},indent=2)+'\n')
        backup=Path(temp)/'previous'
        if installed.exists(): installed.rename(backup)
        try: stage.rename(destination)
        except BaseException:
            if backup.exists(): backup.rename(installed)
            raise
    settings=project_config.settings_directory(project)
    settings.mkdir(exist_ok=True)
    templates={'project.json':'planning/templates/project.json','routing.json':'routing/config.json','host.json':'routing/host.example.json'}
    for name,rel in templates.items():
        target=settings/name
        if not target.exists():
            with target.open('x') as output: output.write((source/'references'/rel).read_text())
    print('Installed '+str(destination))
    print('Existing AGENTS.md and project settings preserved.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('project'); p.add_argument('--update',action='store_true')
    p.add_argument('--host', choices=sorted(HOSTS), default='codex')
    a=p.parse_args()
    try: install(a.project,a.update,a.host)
    except (OSError,ValueError) as exc: raise SystemExit(str(exc))
