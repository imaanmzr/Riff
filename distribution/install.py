#!/usr/bin/env python3
"""Install/update one repository-scoped skill for Codex, Cursor or Claude Code without changing AGENTS.md."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

NAME = 'riff'
LEGACY_NAME = 'engineering-workflow'
HOSTS={'codex':'.agents','cursor':'.cursor','claude':'.claude','vscode':'.github'}

def hashes(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and p.name!='.installation.json' and '__pycache__' not in p.parts}

def install(project, update=False, host="codex"):
    if host not in HOSTS: raise ValueError("Unsupported host")
    project=Path(project).expanduser().resolve()
    if not project.is_dir(): raise ValueError('Project directory does not exist')
    if host == 'cursor':
        for other in ('.agents', '.claude'):
            for name in (NAME, LEGACY_NAME):
                existing = project / other / 'skills' / name
                if (existing / 'SKILL.md').is_file():
                    native_host = 'codex' if other == '.agents' else 'claude'
                    raise ValueError(f'Cursor can already discover {existing}. Update it using --host {native_host}.')
    settings=project/'.engineering-workflow'
    if settings.is_symlink(): raise ValueError('Refusing symlinked project settings')
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
        metadata = installed / '.installation.json'
        if not metadata.exists() or json.loads(metadata.read_text()).get('hashes') != hashes(installed):
            raise ValueError('Installed files changed or are unmanaged. Preserve your edits before updating.')
    parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=parent,prefix='.engineering-stage-') as temp:
        stage=Path(temp)/NAME
        shutil.copytree(source,stage)
        (stage/'.installation.json').write_text(json.dumps({'version':'0.7.0','host':host,'hashes':hashes(stage)},indent=2)+'\n')
        backup=Path(temp)/'previous'
        if installed.exists(): installed.rename(backup)
        try: stage.rename(destination)
        except BaseException:
            if backup.exists(): backup.rename(installed)
            raise
    settings=project/'.engineering-workflow'
    if settings.is_symlink(): raise ValueError('Refusing symlinked project settings')
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
