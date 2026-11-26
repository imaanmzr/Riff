"""Location and ownership of the optional, agent-authored project guide."""
from pathlib import Path
from . import config

BEGIN = b'<!-- riff:onboard -->'
END = b'<!-- /riff:onboard -->'


def records_directory(project, value):
    relative = Path(value)
    directory = (project / relative).resolve()
    if relative.is_absolute() or not directory.is_relative_to(project) or directory == project:
        raise ValueError('Task records directory must be a subdirectory of the project')
    return directory


def guide_path(project):
    settings = config.settings(project)
    if not isinstance(settings, dict):
        raise ValueError('Expected a JSON object in project settings')
    return records_directory(project, settings.get('artifacts_directory', 'docs/riff')) / 'project.md'


def owned_guide(path):
    """Recognize one complete, standalone marker pair; never follow a symlink."""
    if path.is_symlink() or not path.is_file():
        return False
    try:
        data = path.read_bytes()
    except OSError:
        return False
    if data.count(BEGIN) != 1 or data.count(END) != 1:
        return False
    lines = data.splitlines()
    return (BEGIN in lines and END in lines and lines.index(BEGIN) < lines.index(END))
