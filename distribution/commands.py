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

WORKFLOW_COMMANDS = {
    'plan': ('Plan a change', 'Plan this task and stop after plan review'),
    'design': ('Design an interface or change', 'Design an approach for this task'),
    'documentation': ('Advise on or update project docs', 'Handle this documentation request'),
    'architecture': ('Audit existing architecture', 'Audit the architecture for this task'),
    'review': ('Review a change or plan', 'Review this task against its requirements and evidence'),
    'audit': ('Audit a spec, plan, or code change', 'Audit this task independently against its requirements'),
    'execute': ('Execute a reviewed plan', 'Execute the reviewed plan'),
    'resume': ('Resume a saved task', 'Resume this task and reconcile saved state with the working tree'),
    'research': ('Research a bounded question', 'Research this question using the research workflow; distinguish evidence from inference and do not implement changes'),
    'debug': ('Diagnose and reproduce a symptom', 'Diagnose and reproduce this symptom using the debug workflow; do not edit product code or implement a fix'),
    'replan': ('Revise a saved plan', 'Replan this task; preserve prior decisions and snapshots, invalidate affected reviews and do not resume execution'),
}
SAVED_TASK_COMMANDS = ('execute', 'resume', 'replan')


def load(path):
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError(f'Expected a JSON object in {path}')
    return value


def records_directory(project):
    settings = project / '.engineering-workflow' / 'project.json'
    config = load(settings)
    return resolve_records_directory(project, config.get('artifacts_directory', 'docs/work'))


def resolve_records_directory(project, value):
    relative = Path(value)
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
    if __package__:
        from . import core
    else:
        import core
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
    plan.update(core.records.new_fields())
    overrides = {key: getattr(args, key, None) for key in ('profile', 'detail', 'diagrams') if getattr(args, key, None) is not None}
    resolved = core.config.resolve(project, overrides=overrides)
    # Keep presentation provenance outside the reviewed behavioral contract.
    provenance = {key: resolved['provenance'][key] for key in resolved['behavior']}
    plan.update(profile=resolved['profile'], behavior_config=resolved['behavior'], behavior_provenance=provenance,
                config_digest=resolved['digest'], presentation={key: overrides[key] for key in core.config.PRESENTATION if key in overrides})
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix='.riff-new-') as temporary:
        stage = Path(temporary) / args.task
        stage.mkdir()
        (stage / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
        template = (REFERENCES / 'planning/templates/plan.md').read_text()
        (stage / 'plan.md').write_text(template.replace('# Planning record', '# ' + plan['title'], 1), encoding='utf-8')
        plan['authored_digest'] = core.records.authored_digest(stage, plan)
        (stage / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
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
            item = dict(task=directory.name, plan_status=plan.get('status', 'unknown'),
                        execution_status=run.get('status', 'not started'),
                        blockers=run.get('blockers', []) + plan.get('blockers', []))
            if getattr(args, 'details', False):
                if __package__:
                    from . import core
                else:
                    import core
                item['evaluation'] = core.inspect(directory, project)[2]
            results.append(item)
        except (OSError, ValueError, TypeError, AttributeError) as exc:
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
                if 'evaluation' in result:
                    print('  Evaluated: ' + result['evaluation']['evaluated_status'])
                    for issue in result['evaluation']['issues']: print('  - ' + issue['message'])
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
    return subprocess.run([sys.executable, str(script), *arguments, '--project', str(project)], cwd=project).returncode


def prompt(project, args):
    return task_prompt(project, args, args.operation)


def task_prompt(project, args, operation):
    directory = task_directory(project, args.task)
    if not (directory / 'plan.json').is_file():
        raise ValueError(f'Unknown task: {args.task}')
    _, instruction = WORKFLOW_COMMANDS[operation]
    return print_prompt(args.host, f'{instruction} at {json.dumps(str(directory))}.' + workflow_options(args, project, load(directory / 'plan.json')))


def workflow_prompt(project, args):
    if args.task is not None:
        return task_prompt(project, args, args.operation)
    _, instruction = WORKFLOW_COMMANDS[args.operation]
    if not args.subject.strip():
        raise ValueError('Provide a nonempty request')
    location = json.dumps(project.as_posix(), ensure_ascii=False)
    return print_prompt(args.host, f'{instruction} in {location}.\n\n{args.subject}' + workflow_options(args, project))


def workflow_options(args, project, plan=None):
    operation = getattr(args, 'operation', None)
    if operation in ('plan', 'replan', 'debug'):
        if __package__:
            from . import core
        else:
            import core
        resolved = core.config.resolve(project, plan)
        settings = resolved['behavior']
    if operation == 'replan':
        if not args.reason.strip(): raise ValueError('Provide a nonempty replan reason')
        guidance = '\nReason: ' + args.reason
    else:
        guidance = ''
    if operation in ('plan', 'replan'):
        sections = ', '.join(settings['sections']) or 'standard plan sections'
        checks = ', '.join(settings['required_checks']) or 'project-required checks'
        clarification = (
            '\nAfter initial discovery, assess missing intent and important edge cases. '
            'Ask a few focused questions at a time about material gaps before settling dependent decisions; '
            'wait for answers and reuse earlier answers. Record answers in requirements and acceptance examples, '
            'disclose assumptions, and keep unanswered material questions blocking READY. '
            'A clear request needs no manufactured questions.')
        return (guidance + clarification + f"\nWorkflow profile: {resolved['profile']}. Emphasize {sections}. "
                f"Cover these verification obligations: {checks}. Assess risk independently.")
    if operation == 'debug':
        command_timeout = args.command_timeout or settings['debug_command_timeout']
        total_timeout = args.total_timeout or settings['debug_total_timeout']
        return f'\nDiagnostic limits: {command_timeout} seconds per command, {total_timeout} seconds total. Use isolated fixtures, record actual results, and stop all processes you start.'
    if operation == 'research':
        return '\nCreate or reuse a task record before durable reporting. Save structured and narrative reports with stable IDs.'
    return ''


def print_prompt(host, instruction):
    invocation = '$riff' if host == 'codex' else '/riff'
    print('Paste this into your agent chat:')
    print(f'{invocation} {instruction}')
    return 0
