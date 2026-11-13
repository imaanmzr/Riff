#!/usr/bin/env python3
"""Riff: install and configure an engineering workflow in your project."""
import argparse
import json
from pathlib import Path
if __package__:
    from .install import HOSTS, LEGACY_NAME, NAME, install
else:
    from install import HOSTS, LEGACY_NAME, NAME, install


def ask(label, default='', choices=None):
    while True:
        value=input(label + (f' [{default}]' if default else '') + ': ').strip() or default
        if value and (choices is None or value in choices): return value
        print('Choose: '+', '.join(choices) if choices else 'A value is required.')


def number(label, default, minimum):
    while True:
        value=ask(label,str(default))
        try:
            n=int(value)
            if n>=minimum: return n
        except ValueError: pass
        print(f'Enter an integer >= {minimum}.')


def read(path, fallback):
    return json.loads(path.read_text()) if path.exists() else fallback.copy()


def configure(project, host):
    settings=project/'.engineering-workflow'
    config=read(settings/'project.json',{})
    print('Commands are saved as text, never executed by this wizard. Enter - for unknown.')
    for key,label in [('build_command','Build command'),('test_command','Test command')]:
        value=ask(label,config.get(key) or '-')
        config[key]=None if value=='-' else value
    config['artifacts_directory']=ask('Task records directory',config.get('artifacts_directory','docs/work'))
    path=Path(config['artifacts_directory'])
    if path.is_absolute() or '..' in path.parts: raise ValueError('Task directory must be inside the project')
    routing_path=settings/f'routing-{host}.json'
    host_path=settings/'hosts'/f'{host}.json'
    route=read(routing_path,read(settings/'routing.json',{}))
    capability=read(host_path,read(settings/'host.json',{}))
    route['max_parallel']=number('Maximum concurrent agents',route.get('max_parallel',2),1)
    route['token_budget']=number('Total dispatch token budget',route.get('token_budget',100000),1)
    route['task_token_budget']=min(route.get('task_token_budget',10000),route['token_budget'])
    routed=ask('Configure model routing now?','no',['yes','no'])=='yes'
    if routed:
        print('Use exact model IDs available in this app. Enter - to leave a profile unavailable.')
        models={}
        for profile in ('fast','coding','deep_reasoning'):
            value=ask(f'{profile} model',route.get('profiles',{}).get(profile) or '-')
            route.setdefault('profiles',{})[profile]=None if value=='-' else value
            if value!='-': models.setdefault(value,[]).append(profile)
        capability['models']=models
        capability['parallel_agents']=ask('Does this host support parallel agents?','no',['yes','no'])=='yes'
        capability['isolated_workspaces']=ask('Will agents have isolated workspaces?','no',['yes','no'])=='yes'
        capability['available_slots']=number('Total agent slots for this workflow',1,0)
    print('\nProject:',project,'\nApp:',host,'\nRecords:',config['artifacts_directory'])
    if ask('Save configuration?','yes',['yes','no'])=='no': return
    for path,value in [(settings/'project.json',config),(routing_path,route),(host_path,capability)]:
        if path.is_symlink(): raise ValueError('Refusing symlink: '+str(path))
        path.parent.mkdir(parents=True,exist_ok=True)
        temp=path.with_suffix('.tmp')
        with temp.open('x') as stream: stream.write(json.dumps(value,indent=2)+'\n')
        temp.replace(path)
    print('Configured. Use $riff in Codex or /riff in Cursor, VS Code Copilot and Claude Code.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version='Riff 0.6.0')
    parser.add_argument('action',choices=['init','configure','update'])
    parser.add_argument('--project'); parser.add_argument('--host',choices=sorted(HOSTS))
    args=parser.parse_args()
    project=Path(args.project or ask('Project directory',str(Path.cwd()))).expanduser().resolve()
    host=args.host or ask('Agent app','codex',sorted(HOSTS))
    if not project.is_dir(): raise ValueError('Project directory does not exist')
    if args.action in ('init','update'):
        # Cursor can reuse native Codex/Claude copies without duplicate skills.
        target=host
        if host=='cursor':
            for other in ('codex','claude'):
                skills = project / HOSTS[other] / 'skills'
                if any((skills / name / 'SKILL.md').is_file() for name in (NAME, LEGACY_NAME)):
                    target = other
                    break
        dest = project / HOSTS[target] / 'skills' / NAME
        if args.action=='update' or not dest.exists(): install(project,args.action=='update',target)
        else: print('Using existing installation:',dest)
    elif not (project/'.engineering-workflow/project.json').exists():
        raise ValueError('Run init before configure')
    configure(project,host)

def cli():
    try:
        main()
    except (OSError, ValueError, EOFError, KeyboardInterrupt) as exc:
        raise SystemExit('Stopped: ' + str(exc))

if __name__ == '__main__':
    cli()
