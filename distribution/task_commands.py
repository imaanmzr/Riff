"""Local inspection and explicitly requested artifact operations."""
import difflib
import json
from pathlib import Path

if __package__:
    from . import core, commands
else:
    import core, commands


def emit(value, as_json=False):
    print(json.dumps(value, indent=2, ensure_ascii=False) if as_json or not isinstance(value, str) else value)


def export_text(path, content, directory, project, overwrite=False):
    path = Path(path).expanduser().absolute()
    for part in (path, *path.parents):
        if part.is_symlink(): raise ValueError('Refusing symlink output: ' + str(part))
    target = path.resolve()
    plan = core.records.load(directory / 'plan.json')
    protected = {core.records.relative_file(project, name).resolve() for name in plan.get('source_manifest', {})}
    root = commands.records_directory(project)
    for other in root.glob('*/plan.json'):
        if other.parent.is_symlink(): continue
        for name in core.records.load(other).get('source_manifest', {}):
            protected.add(core.records.relative_file(project, name).resolve())
    if target.is_relative_to(commands.records_directory(project).resolve()) or target.is_relative_to((project / '.engineering-workflow').resolve()) or target in protected:
        raise ValueError('Export must not overwrite authoritative task, settings or source records')
    if not path.parent.is_dir(): raise ValueError('Output directory does not exist')
    with path.open('w' if overwrite else 'x', encoding='utf-8', newline='\n') as stream:
        stream.write(content)


def task_operation(project, args):
    directory = commands.task_directory(project, args.task)
    operation = args.action
    if operation == 'migrate':
        emit(core.storage.migrate(directory / 'plan.json', apply=args.apply), True)
        return 0
    if operation in ('checkpoint', 'reconcile'):
        return recovery_operation(project, directory, args)
    if operation == 'diff':
        return compare(directory, args)
    plan, run, report = core.inspect(directory, project)
    if operation in ('show', 'explain', 'check'):
        if args.json:
            emit(dict(task=args.task, title=plan.get('title'), plan=plan if operation == 'show' else None, **report), True)
        elif operation == 'show':
            from riff_core.presentation import render_markdown
            authored = (directory / 'plan.md').read_text(encoding='utf-8')
            settings = core.config.resolve(project, plan)['presentation']
            emit(render_markdown(plan, authored, report, args.detail or settings['detail'], args.diagrams or settings['diagrams']))
        else:
            emit(core.diagnostics.text_report(plan, report))
        return int(operation == 'check' and report['evaluated_status'] != 'READY')
    if operation == 'graph':
        graph = core.records.generated_sections(plan)['graph']
        output = graph.removeprefix('```mermaid\n').removesuffix('\n```') + '\n'
        if args.output: export_text(args.output, output, directory, project, args.overwrite)
        elif args.json: emit({'task': args.task, 'revision': plan.get('revision'), 'mermaid': output}, True)
        else: emit(output)
        return 0
    if operation in ('render', 'export'):
        from riff_core.presentation import render_markdown, render_html
        settings = core.config.resolve(project, plan)['presentation']
        content = render_markdown(plan, (directory / 'plan.md').read_text(encoding='utf-8'), report,
                                  args.detail or settings['detail'], args.diagrams or settings['diagrams'])
        if args.format == 'html':
            content = render_html(content, plan.get('title', args.task), Path(__file__).parent / 'assets',
                                  diagrams=args.diagrams or settings['diagrams'])
        export_text(args.output, content, directory, project, args.overwrite)
        emit('Exported ' + str(Path(args.output).resolve()))
        return 0
    raise ValueError('Unsupported task operation: ' + operation)


def recovery_operation(project, directory, args):
    plan = core.records.load(directory / 'plan.json')
    names = json.loads(Path(args.manifest).read_text(encoding='utf-8'))
    if not isinstance(names, list) or any(not isinstance(n, str) for n in names):
        raise ValueError('Manifest must be an array of relative file names')
    path = directory / 'checkpoint.json'
    # Validate every component, including the output state, before the recovery utility.
    core.records.relative_file(project, path.relative_to(project).as_posix())
    for name in names:
        resolved = core.records.relative_file(project, name)
        if resolved == path or resolved == Path(str(path) + '.lock'):
            raise ValueError('Checkpoint must not fingerprint itself')
    manifest = core.recovery.fingerprint(project, names)
    ctx = dict(task_dir=directory, project=project, effective_behavior=core.config.resolve(project, plan)['behavior'])
    if args.action == 'reconcile':
        emit(core.recovery.reconcile(core.recovery.load(path), plan, manifest, context=ctx), True)
        return 0
    run = core.records.load(directory / 'run.json')
    data = core.recovery.checkpoint(plan, run, manifest)
    if path.exists():
        prior = core.recovery.load(path)
        data['history'] = prior.get('history', []) + [{'previous_run': prior['run'], 'previous_plan': prior['plan'], 'previous_manifest': prior['manifest']}]
    if plan.get('schema_version') == 2:
        data['authored_digest'] = core.records.authored_digest(directory, plan)
        data['config_digest'] = core.records.digest(ctx['effective_behavior'])
    saved = core.recovery.save(path, data, args.expected_generation)
    emit({'generation': saved['generation'], 'state': str(path)}, True)
    return 0


def compare(directory, args):
    current = core.records.load(directory / 'plan.json')
    source = Path(args.against).expanduser().resolve()
    prior_prose = None
    if source.is_dir():
        prior = core.records.load(source / 'plan.json')
        if (source / 'plan.md').exists(): prior_prose = (source / 'plan.md').read_text(encoding='utf-8')
    else:
        prior = core.recovery.load(source)['plan']
    for value in (current, prior):
        if type(value.get('schema_version', 1)) is not int or value.get('schema_version', 1) not in (1, 2):
            raise ValueError('Unsupported schema version in comparison')
    changed = {key: {'before': prior.get(key), 'after': current.get(key)}
               for key in sorted(set(prior) | set(current)) if prior.get(key) != current.get(key) or (key in prior) != (key in current)}
    actual = (directory / 'plan.md').read_text(encoding='utf-8')
    prose = None if prior_prose is None else '\n'.join(difflib.unified_diff(prior_prose.splitlines(), actual.splitlines(), fromfile='snapshot/plan.md', tofile='current/plan.md', lineterm=''))
    value = {'changed_fields': changed, 'prose_diff': prose,
             'prose_comparison': 'unknown: snapshot does not contain prose' if prose is None else 'text comparison; semantic equivalence requires review'}
    emit(value, True)
    return 0


def configuration(project, args):
    if args.config_action == 'show':
        plan = core.records.load(commands.task_directory(project, args.task) / 'plan.json') if args.task else None
        emit(core.config.resolve(project, plan) if args.effective else core.config.settings(project), True)
        return 0
    path = project / '.engineering-workflow' / 'project.json'
    if not path.exists(): raise ValueError('Run riff init before setting configuration')
    original = path.read_bytes()
    current = json.loads(original)
    try: value = json.loads(args.value)
    except json.JSONDecodeError: value = args.value
    core.config.validate_value(args.key, value)
    if args.key == 'profile' and value not in core.config.profiles(project): raise ValueError('Unknown profile: ' + value)
    current[args.key] = value
    core.storage.atomic_json(path, current, original)
    emit('Saved ' + args.key + '; reviewed behavioral changes require replan.')
    return 0


def profile(project, args):
    available = core.config.profiles(project)
    if args.profile_action == 'list': emit(available, True)
    elif args.name not in available: raise ValueError('Unknown profile: ' + args.name)
    else: emit({'name': args.name, **available[args.name]}, True)
    return 0
