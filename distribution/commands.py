"""Project task commands used by the Riff terminal interface."""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if __package__:
    from .install import HOSTS, NAME
else:
    from install import HOSTS, NAME

REFERENCES = Path(__file__).resolve().parent / 'skills' / NAME / 'references'


def load(path):
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f'Expected a JSON object in {path}')
    return value


def records_directory(project):
    settings = project / '.engineering-workflow' / 'project.json'
    config = load(settings)
    relative = Path(config.get('artifacts_directory', 'docs/work'))
    directory = (project / relative).resolve()
    if relative.is_absolute() or not directory.is_relative_to(project) or directory == project:
        raise ValueError('Task records directory must be a subdirectory of the project')
    return directory


def task_directory(project, task):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', task):
        raise ValueError('Task ID must contain 1–80 letters, digits, underscores or hyphens')
    root = records_directory(project)
    directory = root / task
    if directory.is_symlink():
        raise ValueError(f'Task directory is a symlink: {directory}')
    return directory


def new_task(project, args):
    destination = task_directory(project, args.task)
    if destination.exists():
        raise ValueError(f'Task already exists: {args.task}')
    source_revision = None
    if shutil.which('git'):
        result = subprocess.run(['git', '-C', str(project), 'rev-parse', 'HEAD'],
                                capture_output=True, text=True)
        if result.returncode == 0:
            source_revision = result.stdout.strip()
    plan = dict(task_id=args.task, title=args.title or args.task, route=args.route,
                status='DRAFT', revision=1, source_revision=source_revision,
                requirements=[], tasks=[], reviews=[],
                unresolved_questions=['Inspect the working tree and define acceptance criteria'])
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix='.riff-new-') as temporary:
        stage = Path(temporary) / args.task
        stage.mkdir()
        (stage / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
        template = (REFERENCES / 'planning/templates/plan.md').read_text()
        (stage / 'plan.md').write_text(template.replace('# Planning record', '# ' + plan['title'], 1))
        # mkdir exclusively claims the destination so concurrent creation cannot overwrite it.
        destination.mkdir()
        try:
            for source in stage.iterdir():
                source.rename(destination / source.name)
        except BaseException:
            shutil.rmtree(destination)
            raise
    print(f'Created task {args.task} at {destination}')
    print(f'Next: riff prompt {args.task} --action plan --host codex')


def status(project, args):
    root = records_directory(project)
    if args.task:
        directories = [task_directory(project, args.task)]
        if not directories[0].is_dir():
            raise ValueError(f'Unknown task: {args.task}')
    else:
        directories = sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith('.')) if root.exists() else []
    results = []
    for directory in directories:
        if directory.is_symlink():
            continue
        try:
            plan = load(directory / 'plan.json')
            run_path = directory / 'run.json'
            run = load(run_path) if run_path.exists() else {}
            results.append(dict(task=directory.name, plan_status=plan.get('status', 'unknown'),
                                execution_status=run.get('status', 'not started'),
                                blockers=run.get('blockers', []) + plan.get('blockers', [])))
        except (OSError, ValueError) as exc:
            results.append(dict(task=directory.name, error=str(exc)))
    if args.json:
        print(json.dumps(results, indent=2))
    elif not results:
        print('No tasks found. Create one with riff new TASK.')
    else:
        for result in results:
            if 'error' in result:
                print(f"{result['task']}: unreadable record — {result['error']}")
            else:
                print(f"{result['task']}: plan={result['plan_status']}, execution={result['execution_status']}, blockers={len(result['blockers'])}")
    return int(any('error' in result for result in results))


def doctor(project, args):
    issues = []
    settings = project / '.engineering-workflow'
    try:
        records_directory(project)
        print('Project configuration: OK')
    except (OSError, ValueError) as exc:
        issues.append(f'Project configuration: {exc}. Run riff init.')
    hosts = [args.host] if args.host else list(HOSTS)
    found = False
    for host in hosts:
        folders = [HOSTS[host]]
        if host == 'cursor':
            folders += ['.agents', '.claude']
        paths = [project / folder / 'skills' / NAME / 'SKILL.md' for folder in folders]
        installed = [path for path in paths if path.is_file()]
        if installed:
            found = True
            print(f'{host}: {installed[0]}')
    if not found:
        issues.append('No Riff skill found for the selected host(s). Run riff init.')
    for issue in issues:
        print(issue)
    print('Model availability and live editor discovery require confirmation in the host.')
    return int(bool(issues))


def run_utility(project, args):
    directory = task_directory(project, args.task)
    plan = directory / 'plan.json'
    run = directory / 'run.json'
    if args.action == 'validate':
        script = REFERENCES / ('execution/gates.py' if args.execution else 'planning/validate.py')
        arguments = [str(plan)] + ([str(run)] if args.execution else [])
    else:
        script = REFERENCES / 'routing/router.py'
        settings = project / '.engineering-workflow'
        config = settings / f'routing-{args.host}.json'
        host = settings / 'hosts' / f'{args.host}.json'
        if not config.exists():
            config = settings / 'routing.json'
        if not host.exists():
            host = settings / 'host.json'
        arguments = ['--plan', str(plan), '--run', str(run), '--config', str(config), '--host', str(host)]
    return subprocess.run([sys.executable, str(script), *arguments], cwd=project).returncode


def prompt(project, args):
    directory = task_directory(project, args.task)
    if not (directory / 'plan.json').is_file():
        raise ValueError(f'Unknown task: {args.task}')
    invocation = '$riff' if args.host == 'codex' else '/riff'
    operations = {'plan': 'Plan this task and stop after plan review',
                  'execute': 'Execute the reviewed plan',
                  'resume': 'Resume this task and reconcile saved state with the working tree',
                  'audit': 'Audit this task independently against its requirements'}
    print('Paste this into your agent chat:')
    print(f'{invocation} {operations[args.operation]} at {json.dumps(str(directory))}.')
    return 0
