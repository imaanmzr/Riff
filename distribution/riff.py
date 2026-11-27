#!/usr/bin/env python3
"""Riff: install and configure an engineering workflow in your project."""
import argparse
import json
from pathlib import Path
if __package__:
    from . import commands, task_commands, core
    from .git_visibility import GitVisibility
    from .install import HOSTS, LEGACY_NAME, NAME, install, installation_host
    from .version import VERSION
else:
    import commands, task_commands, core
    from git_visibility import GitVisibility
    from install import HOSTS, LEGACY_NAME, NAME, install, installation_host
    from version import VERSION


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
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else fallback.copy()


def configure(project, host, git, git_mode=None):
    settings=core.config.settings_directory(project)
    config=read(settings/'project.json',{})
    print('Commands are saved as text, never executed by this wizard. Enter - for unknown.')
    for key,label in [('build_command','Build command'),('test_command','Test command')]:
        value=ask(label,config.get(key) or '-')
        config[key]=None if value=='-' else value
    config['artifacts_directory']=ask('Task records directory',config.get('artifacts_directory','docs/riff'))
    records = commands.resolve_records_directory(project, config['artifacts_directory'])
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
    if git and git_mode is None:
        git_mode = ask('Git visibility for the Riff skill, settings and task records (local/track/unchanged)',
                       'unchanged', ['local', 'track', 'unchanged'])
    print('\nProject:',project,'\nApp:',host,'\nRecords:',config['artifacts_directory'])
    if ask('Save configuration?','yes',['yes','no'])=='no': return
    for path,value in [(settings/'project.json',config),(routing_path,route),(host_path,capability)]:
        if path.is_symlink(): raise ValueError('Refusing symlink: '+str(path))
        path.parent.mkdir(parents=True,exist_ok=True)
        temp=path.with_suffix('.tmp')
        with temp.open('x') as stream: stream.write(json.dumps(value,indent=2)+'\n')
        temp.replace(path)
    if git and git_mode in ('local', 'track'):
        git.apply(git_mode, records)
    elif git and git.is_local():
        git.apply('local', records)
    print('Configured. Use $riff in Codex or /riff in Cursor, VS Code Copilot and Claude Code.')


def build_parser():
    parser = argparse.ArgumentParser(
        prog='riff',
        description='Install Riff, prepare agent workflow prompts, and inspect saved tasks.',
        epilog='Examples:\n  riff init --host cursor\n  riff plan "Add partial refunds" --host cursor\n  riff design "Compare retry interfaces"\n  riff review --task refunds\n  riff status\n\nRun riff COMMAND --help for command options.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--version', action='version', version='Riff ' + VERSION)
    subparsers = parser.add_subparsers(dest='action', title='commands', metavar='COMMAND')
    onboard = subparsers.add_parser('onboard', help='Understand a project and save its guide (prints an agent prompt)')
    onboard.add_argument('--project', help='Project directory (default: current directory)')
    onboard.add_argument('--host', choices=sorted(HOSTS), default='codex', help='Agent app (default: codex)')
    add_elicitation_options(onboard)
    onboard.set_defaults(handler=commands.onboard)
    descriptions = {
        'init': 'Install the project skill and open the setup wizard',
        'configure': 'Edit project commands, model mappings and budgets',
        'update': 'Update the project skill from this Riff installation',
        'doctor': 'Check project configuration and installed skill locations',
        'new': 'Create draft planning records for a task',
        'status': 'Show saved plan and execution status',
        'prompt': 'Print a task prompt to paste into your agent chat',
        'validate': 'Check plan structure or execution evidence records',
        'route': 'Propose assignments using saved tasks and host configuration',
    }
    for action, description in descriptions.items():
        command = subparsers.add_parser(action, help=description, description=description)
        command.add_argument('--project', help='Project directory (default: current directory)')
        if action in ('init', 'configure'):
            command.add_argument('--git', choices=('local', 'track'),
                                 help='Keep Riff files local or make them eligible for Git tracking')
        if action == 'configure':
            command.add_argument('--untrack', action='store_true',
                                 help='With --git local, stage removal of tracked Riff files and keep local copies')
        if action in ('init', 'configure', 'update', 'doctor', 'prompt', 'route'):
            command.add_argument('--host', choices=sorted(HOSTS), required=action == 'route',
                                 default='codex' if action == 'prompt' else None,
                                 help='Agent app used by this project')
        if action in ('new', 'prompt', 'validate', 'route'):
            command.add_argument('task', help='Task ID, such as partial-refunds')
        if action == 'new':
            command.add_argument('--title', help='Human-readable task title')
            command.add_argument('--route', choices=['small', 'standard', 'complex', 'critical'], default='standard')
            command.add_argument('--profile', help='Workflow profile (default: project setting or feature)')
            command.add_argument('--detail', choices=['concise', 'full'])
            command.add_argument('--diagrams', choices=['auto', 'none'])
        if action == 'status':
            command.add_argument('task', nargs='?', help='Task ID (default: all tasks)')
            command.add_argument('--json', action='store_true', help='Emit machine-readable JSON')
            command.add_argument('--details', action='store_true', help='Show every task, review history, and gate issue (default: progress summary)')
        if action == 'prompt':
            command.add_argument('--action', dest='operation', choices=['plan', 'execute', 'resume', 'audit', 'elicit'], default='plan')
            add_elicitation_options(command)
        if action == 'validate':
            command.add_argument('--execution', action='store_true', help='Validate plan.json and run.json together')
    for operation, (description, _) in commands.WORKFLOW_COMMANDS.items():
        aliases = ['docs'] if operation == 'documentation' else []
        command = subparsers.add_parser(
            operation, aliases=aliases, help=f'{description} (prints an agent prompt)',
            description=f'{description}. Paste the resulting prompt into your agent chat.',
        )
        command.set_defaults(operation=operation, handler=commands.workflow_prompt)
        command.add_argument('--project', help='Project directory (default: current directory)')
        command.add_argument('--host', choices=sorted(HOSTS), default='codex',
                             help='Agent app (default: codex)')
        add_elicitation_options(command, standalone=operation == 'elicit')
        if operation == 'replan':
            command.add_argument('--reason', required=True, help='Reason to revise the saved plan')
        if operation == 'debug':
            command.add_argument('--command-timeout', type=positive)
            command.add_argument('--total-timeout', type=positive)
        if operation in commands.SAVED_TASK_COMMANDS:
            command.add_argument('task', help='Saved task ID')
        else:
            target = command.add_mutually_exclusive_group(required=True)
            target.add_argument('subject', nargs='?', help='Request to send to the agent')
            target.add_argument('--task', help='Use an existing task ID')
    for action in ('show', 'explain', 'check', 'graph', 'render', 'diff', 'checkpoint', 'reconcile', 'migrate'):
        aliases = ['export'] if action == 'render' else []
        command = subparsers.add_parser(action, aliases=aliases, help={
            'show': 'Read a plan', 'explain': 'Explain current blockers', 'check': 'Check records and live evidence',
            'graph': 'Export task dependencies', 'render': 'Export Markdown or offline HTML',
            'diff': 'Compare an explicit snapshot', 'checkpoint': 'Save a generation-checked checkpoint',
            'reconcile': 'Inspect a recovery proposal', 'migrate': 'Preview or apply schema migration'}[action])
        command.set_defaults(handler=task_commands.task_operation)
        command.add_argument('task')
        command.add_argument('--project')
        command.add_argument('--json', action='store_true')
        if action in ('show', 'render'):
            command.add_argument('--detail', choices=['concise', 'full'])
            command.add_argument('--diagrams', choices=['auto', 'none'])
        if action in ('graph', 'render'):
            command.add_argument('--output', required=action == 'render')
            command.add_argument('--overwrite', action='store_true')
        if action == 'render': command.add_argument('--format', choices=['markdown', 'html'], default='markdown')
        if action == 'diff': command.add_argument('--against', required=True)
        if action == 'migrate':
            command.add_argument('--apply', action='store_true')
            command.add_argument('--manifest', help='Optional JSON array of project-relative source files to bind during a legacy upgrade')
        if action in ('checkpoint', 'reconcile'): command.add_argument('--manifest', required=True)
        if action == 'checkpoint': command.add_argument('--expected-generation', required=True, type=nonnegative)
    config = subparsers.add_parser('config', help='Inspect or set validated project settings')
    subs = config.add_subparsers(dest='config_action', required=True)
    for operation in ('show', 'set'):
        command = subs.add_parser(operation)
        command.set_defaults(handler=task_commands.configuration)
        command.add_argument('--project')
        command.add_argument('--json', action='store_true')
        if operation == 'show':
            command.add_argument('--effective', action='store_true')
            command.add_argument('--task')
        else:
            command.add_argument('key')
            command.add_argument('value')
    profiles = subparsers.add_parser('profile', help='Inspect workflow profiles')
    subs = profiles.add_subparsers(dest='profile_action', required=True)
    for operation in ('list', 'show'):
        command = subs.add_parser(operation)
        command.set_defaults(handler=task_commands.profile)
        command.add_argument('--project')
        command.add_argument('--json', action='store_true')
        if operation == 'show': command.add_argument('name')
    return parser


def add_elicitation_options(parser, standalone=False):
    if not standalone:
        parser.add_argument('--elicit', action='store_true',
                            help='Elicit decisions deeply before dependent work, then continue within this action\'s gates')
    parser.add_argument('--focus', type=nonempty,
                        help='Decision or subproblem to examine (requires elicit or --elicit)')


def nonempty(value):
    if not value.strip():
        raise argparse.ArgumentTypeError('Focus must be nonempty')
    return value


def nonnegative(value):
    try: number = int(value)
    except ValueError: raise argparse.ArgumentTypeError('Expected an integer')
    if number < 0: raise argparse.ArgumentTypeError('Must be nonnegative')
    return number


def positive(value):
    result = nonnegative(value)
    if result == 0: raise argparse.ArgumentTypeError('Must be positive')
    return result


def main():
    parser = build_parser()
    args = parser.parse_args()
    if (getattr(args, 'focus', None) is not None
            and getattr(args, 'operation', None) != 'elicit'
            and not getattr(args, 'elicit', False)):
        parser.error('--focus requires elicit or --elicit')
    if args.action is None:
        parser.print_help()
        return
    if args.action not in ('init', 'configure', 'update'):
        project = Path(args.project or Path.cwd()).expanduser().resolve()
        if not project.is_dir():
            raise ValueError('Project directory does not exist')
        handlers = {'new': commands.new_task, 'status': commands.status,
                    'doctor': commands.doctor, 'prompt': commands.prompt,
                    'validate': commands.run_utility, 'route': commands.run_utility}
        handler = getattr(args, 'handler', None) or handlers[args.action]
        raise SystemExit(handler(project, args) or 0)
    git_mode = getattr(args, 'git', None)
    untrack = getattr(args, 'untrack', False)
    if untrack and git_mode != 'local':
        parser.error('--untrack requires --git local')
    project_choice = args.project
    if project_choice is None:
        project_choice = str(Path.cwd()) if git_mode else ask('Project directory', str(Path.cwd()))
    project=Path(project_choice).expanduser().resolve()
    if not project.is_dir(): raise ValueError('Project directory does not exist')
    git = GitVisibility.discover(project)
    if git_mode and git is None:
        raise ValueError('Git visibility requires a Git working tree')
    if args.action == 'configure' and git_mode:
        if not (core.config.settings_directory(project) / 'project.json').is_file():
            raise ValueError('Run init before configure')
        git.apply(git_mode, commands.records_directory(project), untrack=untrack)
        return
    host=args.host or ask('Agent app','codex',sorted(HOSTS))
    if args.action in ('init','update'):
        # Cursor can reuse native Codex/Claude copies without duplicate skills.
        target=installation_host(project, host)
        dest = project / HOSTS[target] / 'skills' / NAME
        if args.action=='update' or not dest.exists(): install(project,args.action=='update',target)
        else: print('Using existing installation:',dest)
    elif not (core.config.settings_directory(project) / 'project.json').exists():
        raise ValueError('Run init before configure')
    if args.action == 'init' and git_mode:
        git.apply(git_mode, commands.records_directory(project))
    configure(project,host,git,git_mode)

def cli():
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError, EOFError, KeyboardInterrupt) as exc:
        raise SystemExit('Stopped: ' + str(exc))

if __name__ == '__main__':
    cli()
