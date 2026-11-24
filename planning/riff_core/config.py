"""Validated workflow settings; presentation never changes review policy."""
import copy
from pathlib import Path
from .records import load, digest

PROFILES = {
    'feature': {'sections': ['problem', 'behavior', 'contracts'], 'required_checks': ['acceptance', 'regression']},
    'bug': {'sections': ['symptom', 'reproduction', 'hypotheses'], 'required_checks': ['reproduction', 'regression']},
    'refactor': {'sections': ['boundaries', 'compatibility'], 'required_checks': ['behavior preservation', 'regression']},
    'migration': {'sections': ['compatibility', 'rollout', 'rollback'], 'required_checks': ['migration', 'rollback', 'regression']},
    'documentation': {'sections': ['reader', 'examples'], 'required_checks': ['example accuracy', 'links']},
    'architecture': {'sections': ['constraints', 'alternatives', 'trade-offs'], 'required_checks': ['source evidence', 'boundary review']},
    'research': {'sections': ['question', 'sources', 'counterevidence', 'uncertainty'], 'required_checks': ['source quality', 'question coverage']},
}
DEFAULTS = {'build_command': None, 'test_command': None, 'architecture_constraints': [],
            'domain_invariants': [], 'sections': [], 'required_checks': [],
            'debug_command_timeout': 60, 'debug_total_timeout': 300}
PRESENTATION = {'detail': 'full', 'diagrams': 'auto'}
SETTINGS_DIRECTORIES = ('.riff', '.engineering-workflow')


def settings_directory(project):
    """Select one settings tree without moving or merging existing files."""
    current, legacy = (Path(project) / name for name in SETTINGS_DIRECTORIES)
    for path in (current, legacy):
        if path.is_symlink():
            raise ValueError('Refusing symlinked project settings: ' + str(path))
        if path.exists() and not path.is_dir():
            raise ValueError('Project settings path must be a directory: ' + str(path))
    if current.exists() and legacy.exists():
        raise ValueError('Both .riff and .engineering-workflow settings exist. '
                         'Preserve your files and resolve the duplicate settings directories before continuing.')
    return legacy if legacy.exists() else current


def settings(project):
    path = settings_directory(project) / 'project.json'
    return load(path) if path.exists() else {}


def validate_value(key, value):
    if key in ('build_command', 'test_command'):
        if value is not None and not isinstance(value, str):
            raise ValueError(key + ' must be text or null')
    elif key in ('architecture_constraints', 'domain_invariants', 'sections', 'required_checks'):
        if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
            raise ValueError(key + ' must be an array of nonempty strings')
    elif key in ('debug_command_timeout', 'debug_total_timeout'):
        if type(value) is not int or value <= 0:
            raise ValueError(key + ' must be a positive integer')
    elif key == 'detail':
        if value not in ('concise', 'full'): raise ValueError('detail must be concise or full')
    elif key == 'diagrams':
        if value not in ('auto', 'none'): raise ValueError('diagrams must be auto or none')
    elif key == 'profile':
        if not isinstance(value, str) or not value.strip(): raise ValueError('profile must be nonempty text')
    elif key == 'profiles':
        if not isinstance(value, dict): raise ValueError('profiles must be an object')
        for name, profile in value.items():
            validate_value('profile', name)
            if not isinstance(profile, dict): raise ValueError('profile values must be objects')
            for field, item in profile.items():
                if field not in DEFAULTS: raise ValueError('Unknown profile setting: ' + field)
                validate_value(field, item)
    else:
        raise ValueError('Unsupported setting: ' + key + '; routing budgets use configure')


def profiles(project):
    result = copy.deepcopy(PROFILES)
    custom = settings(project).get('profiles', {})
    validate_value('profiles', custom)
    for name, values in custom.items():
        result.setdefault(name, {}).update(values)
    return result


def resolve(project, plan=None, overrides=None):
    plan, overrides = plan or {}, overrides or {}
    config = settings(project)
    name = overrides.get('profile') or plan.get('profile') or config.get('profile', 'feature')
    available = profiles(project)
    if name not in available: raise ValueError('Unknown profile: ' + str(name))
    behavior, presentation = copy.deepcopy(DEFAULTS), dict(PRESENTATION)
    provenance = {key: 'built-in' for key in (*behavior, *presentation)}
    layers = [('profile:' + name, available[name]), ('project', config),
              ('task', plan.get('task_overrides', {})), ('task presentation', plan.get('presentation', {})),
              ('invocation', overrides)]
    for origin, layer in layers:
        if not isinstance(layer, dict): raise ValueError(origin + ' settings must be an object')
        for key, value in layer.items():
            if key in behavior and origin != 'task presentation':
                validate_value(key, value)
                behavior[key] = copy.deepcopy(value)
                provenance[key] = origin
            elif key in presentation:
                validate_value(key, value)
                presentation[key] = value
                provenance[key] = origin
    provenance['profile'] = ('invocation' if overrides.get('profile') else 'task' if plan.get('profile')
                             else 'project' if config.get('profile') else 'built-in')
    return {'profile': name, 'behavior': behavior, 'provenance': provenance,
            'presentation': presentation, 'digest': digest(behavior)}


def context(plan_path, project=None):
    """Locate actual inputs; never trust a root path embedded in a plan."""
    plan_path = Path(plan_path).resolve()
    if project is None:
        project = next((p for p in plan_path.parents
                        if any((p / name / 'project.json').is_file() for name in SETTINGS_DIRECTORIES)
                        or (p / '.git').exists()), None)
    if project is None:
        raise ValueError('Cannot locate project; supply --project')
    project = Path(project).resolve()
    if not plan_path.is_relative_to(project): raise ValueError('Plan is outside project')
    plan = load(plan_path)
    return {'task_dir': plan_path.parent, 'project': project,
            'effective_behavior': resolve(project, plan)['behavior']}
