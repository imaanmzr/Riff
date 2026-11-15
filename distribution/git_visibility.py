"""Manage local Git exclusions and tracking for a project's Riff files."""
import hashlib
import os
from pathlib import Path
import re
import subprocess

if __package__:
    from .install import HOSTS, LEGACY_NAME, NAME
else:
    from install import HOSTS, LEGACY_NAME, NAME


class GitVisibility:
    def __init__(self, project, prefix, exclude):
        self.project = project
        self.prefix = prefix
        self.exclude = exclude
        key = hashlib.sha256(prefix.encode('utf-8', errors='surrogateescape')).hexdigest()[:16] if prefix else 'root'
        self.begin = f'# >>> Riff local files ({key})'.encode()
        self.end = f'# <<< Riff local files ({key})'.encode()

    @classmethod
    def discover(cls, project):
        try:
            result = subprocess.run(
                ['git', '-C', str(project), 'rev-parse', '--is-inside-work-tree',
                 '--show-prefix', '--path-format=absolute', '--git-path', 'info/exclude'],
                capture_output=True,
            )
        except FileNotFoundError:
            return None
        fields = result.stdout.decode('utf-8', errors='surrogateescape').rstrip('\r\n').split('\n')
        fields = [field.rstrip('\r') for field in fields]
        if result.returncode or len(fields) != 3 or fields[0] != 'true':
            return None
        return cls(project, fields[1], Path(fields[2]))

    def read(self):
        if self.exclude.is_symlink():
            raise ValueError(f'Refusing symlinked Git exclude file: {self.exclude}')
        return self.exclude.read_bytes() if self.exclude.exists() else b''

    def block(self, content):
        pattern = (rb'^' + re.escape(self.begin) + rb'\r?\n.*?^' +
                   re.escape(self.end) + rb'(?:\r?\n|\Z)')
        return re.search(pattern, content, re.MULTILINE | re.DOTALL)

    def is_local(self):
        return self.block(self.read()) is not None

    def git(self, *arguments, input_data=None, allowed=(0,), literal=True, directory=None):
        options = ['--literal-pathspecs'] if literal else []
        result = subprocess.run(
            ['git', *options, '-C', str(directory or self.project), *arguments],
            input=input_data, capture_output=True,
        )
        if result.returncode not in allowed:
            raise ValueError(result.stderr.decode(errors='replace').strip() or 'Git command failed')
        return result.stdout

    def untrack_paths(self, entries, owned_paths, record_path):
        index = {}
        for entry in entries.split(b'\0')[:-1]:
            details, path = entry.split(b'\t', 1)
            mode, _, stage = details.split()
            index.setdefault(path, []).append((mode, stage))

        owned = tuple(os.fsencode(path) + b'/' for path in owned_paths)
        records = os.fsencode(record_path) + b'/'
        task_dirs = set()
        for path in index:
            if not path.startswith(records):
                continue
            task, separator, name = path[len(records):].partition(b'/')
            if separator and name in (b'plan.json', b'plan.md'):
                task_dirs.add(task)

        selected = []
        for path, stages in index.items():
            scope = path.startswith(owned)
            if path.startswith(records):
                task, separator, _ = path[len(records):].partition(b'/')
                if separator and task not in task_dirs:
                    directory = self.project / os.fsdecode(records + task)
                    if not directory.is_symlink() and any(
                        (directory / name).is_file() for name in ('plan.json', 'plan.md')
                    ):
                        task_dirs.add(task)
                scope = scope or (separator and task in task_dirs)
            if not scope:
                continue
            if any(stage != b'0' for _, stage in stages):
                raise ValueError('Resolve Git conflicts in the Riff files before untracking them')
            if stages[0][0] != b'160000':
                selected.append(path)
        return selected

    def remove_from_index(self, paths):
        if not paths:
            print('No tracked Riff files found to untrack.')
            return
        root = os.fsdecode(self.git('rev-parse', '--show-toplevel').rstrip(b'\r\n'))
        prefix = b'./' + os.fsencode(self.prefix)
        paths = [prefix + path for path in paths]
        path_list = b'\0'.join(paths) + b'\0'
        ignored = self.git('check-ignore', '--no-index', '--stdin', '-z',
                           input_data=path_list, allowed=(0, 1), literal=False, directory=root)
        if set(paths) != set(ignored.split(b'\0')[:-1]):
            raise ValueError('Git still includes some Riff paths. Review existing ignore rules before untracking.')
        self.git('rm', '--quiet', '--cached', '--pathspec-from-file=-', '--pathspec-file-nul',
                 input_data=path_list, directory=root)
        print(f'Staged removal of {len(paths)} Riff file(s) from Git. Local copies remain on disk.')
        print('Review the staged removals with git diff --cached --name-status.')

    def apply(self, mode, records, *, untrack=False):
        record_path = records.relative_to(self.project)
        if any(part.lower() == '.git' for part in record_path.parts):
            raise ValueError('Task records directory must be outside Git metadata')
        owned_paths = {
            '.engineering-workflow',
            *(f'{folder}/skills/{name}' for folder in HOSTS.values()
              for name in (NAME, LEGACY_NAME)),
        }
        paths = sorted({*owned_paths, record_path.as_posix()})
        if any('\r' in path or '\n' in path for path in paths):
            raise ValueError('Riff Git exclusions require single-line paths')

        original = self.read()
        if mode == 'track' and self.block(original) is None:
            print('Git visibility: track. Existing Git ignore rules still apply.')
            return

        tracked = b''
        selected = []
        if mode == 'local':
            tracked = self.git('ls-files', '--stage', '-z', '--', *paths)
            if untrack:
                selected = self.untrack_paths(tracked, owned_paths, record_path.as_posix())
        self.exclude.parent.mkdir(parents=True, exist_ok=True)
        lock = self.exclude.with_name(self.exclude.name + '.lock')
        stream = lock.open('xb')
        replaced = False
        try:
            with stream:
                content = self.read()
                block = self.block(content)
                replacement = b''
                if mode == 'local':
                    newline = b'\r\n' if b'\r\n' in content else b'\n'
                    rules = content[block.start():block.end()].splitlines()[1:-1] if block else []
                    for path in paths:
                        escaped = re.sub(r'([\\*?\[\] ])', r'\\\1', self.prefix + path)
                        rules.append(f'/{escaped}/'.encode('utf-8', errors='surrogateescape'))
                    replacement = newline.join([self.begin, *dict.fromkeys(rules), self.end, b''])
                if block:
                    updated = content[:block.start()] + replacement + content[block.end():]
                else:
                    updated = replacement + content
                if updated != content:
                    stream.write(updated)
            if updated != content:
                os.replace(lock, self.exclude)
                replaced = True
        finally:
            if not replaced:
                lock.unlink(missing_ok=True)

        if mode == 'local':
            print(f'Git visibility: local. Added local exclusions for Riff settings, skills and {record_path.as_posix()}.')
            if untrack:
                self.remove_from_index(selected)
            elif tracked:
                print('Some Riff paths are already tracked. To untrack them, run riff configure --git local --untrack.')
        else:
            print('Git visibility: track. Existing Git ignore rules still apply.')
