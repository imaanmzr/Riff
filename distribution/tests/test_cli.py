import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / 'riff.py'
INSTALLER = ROOT / 'install_cli.py'


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        self.cwd = self.project / 'outside'
        self.cwd.mkdir()
        settings = self.project / '.riff'
        settings.mkdir()
        (settings / 'project.json').write_text('{"artifacts_directory":"docs/work"}')

    def run_cli(self, *arguments, project=None, answers=None):
        return subprocess.run([sys.executable, str(CLI), *arguments,
                               '--project', str(project or self.project)],
                              input=answers, capture_output=True, text=True, cwd=self.cwd)

    def git(self, *arguments, project=None, check=True):
        return subprocess.run(['git', '-C', str(project or self.project), *arguments],
                              capture_output=True, text=True, check=check)

    def test_new_status_prompt_and_plan_validation(self):
        result = self.run_cli('new', 'refunds', '--title', 'Partial refunds')
        self.assertEqual(0, result.returncode, result.stderr)
        plan = self.project / 'docs/work/refunds/plan.json'
        self.assertEqual('DRAFT', json.loads(plan.read_text())['status'])
        status = self.run_cli('status', '--json')
        self.assertEqual('refunds', json.loads(status.stdout)[0]['task'])
        prompt = self.run_cli('prompt', 'refunds', '--host', 'cursor')
        self.assertIn('/riff Plan', prompt.stdout)
        self.assertEqual(0, self.run_cli('validate', 'refunds').returncode)

    def test_default_records_directory_and_existing_configuration(self):
        settings = self.project / '.riff/project.json'
        settings.write_text('{}')
        self.assertEqual(0, self.run_cli('new', 'fresh').returncode)
        self.assertTrue((self.project / 'docs/riff/fresh/plan.json').is_file())
        self.assertFalse((self.project / 'docs/work').exists())
        # Existing explicit paths are neither relocated nor replaced.
        for directory in ('docs/work', 'notes/tasks'):
            settings.write_text(json.dumps({'artifacts_directory': directory}))
            self.assertEqual(0, self.run_cli('new', 'existing').returncode)
            self.assertTrue((self.project / directory / 'existing/plan.json').is_file())
            self.assertEqual('existing', json.loads(self.run_cli('status', '--json').stdout)[0]['task'])
            self.assertEqual(directory, json.loads(settings.read_text())['artifacts_directory'])

    def test_workflow_commands_print_host_requests(self):
        operations = {
            'plan': 'Plan this task',
            'design': 'Design an approach',
            'docs': 'Handle this documentation request',
            'documentation': 'Handle this documentation request',
            'architecture': 'Audit the architecture',
            'review': 'Review this task',
            'audit': 'Audit this task independently',
        }
        for operation, instruction in operations.items():
            with self.subTest(operation=operation):
                result = self.run_cli(operation, 'Examine refund handling', '--host', 'vscode')
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertIn(f'/riff {instruction}', result.stdout)
                self.assertIn(self.project.resolve().as_posix(), result.stdout)
                self.assertIn('Examine refund handling', result.stdout)
        self.assertFalse((self.project / 'docs/work').exists())

    def test_workflow_commands_reuse_saved_tasks(self):
        self.assertEqual(0, self.run_cli('new', 'refunds').returncode)
        plan = self.project / 'docs/work/refunds/plan.json'
        original = plan.read_bytes()
        for operation, arguments in {
            'plan': ('--task', 'refunds'),
            'execute': ('refunds',),
            'resume': ('refunds',),
            'audit': ('--task', 'refunds'),
        }.items():
            with self.subTest(operation=operation):
                direct = self.run_cli(operation, *arguments)
                legacy = self.run_cli('prompt', 'refunds', '--action', operation)
                self.assertEqual(0, direct.returncode, direct.stderr)
                self.assertEqual(legacy.stdout, direct.stdout)
        review = self.run_cli('review', '--task', 'refunds')
        self.assertEqual(0, review.returncode, review.stderr)
        self.assertIn('$riff Review this task', review.stdout)
        self.assertEqual(original, plan.read_bytes())
        self.assertFalse(plan.with_name('run.json').exists())
        self.assertIn('Unknown task: missing', self.run_cli('execute', 'missing').stderr)

    def test_workflow_commands_reject_missing_or_conflicting_targets(self):
        for arguments in ((), ('Examine refunds', '--task', 'refunds')):
            with self.subTest(arguments=arguments):
                self.assertEqual(2, self.run_cli('design', *arguments).returncode)

    @unittest.skipUnless(shutil.which('git'), 'Git executable required')
    def test_git_archive_keeps_shell_launchers_executable_with_autocrlf(self):
        self.git('init', '--quiet')
        self.git('config', 'core.autocrlf', 'true')
        launchers = ('riff', 'distribution/riff')
        for name in ('.gitattributes', *launchers):
            target = self.project / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        self.git('add', '--', '.gitattributes', *launchers)
        self.git('update-index', '--chmod=+x', '--', *launchers)
        self.git('-c', 'user.name=Riff Test', '-c', 'user.email=riff@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Track shell launchers')
        archive = self.project / 'source.tar'
        self.git('archive', '--format=tar', f'--output={archive}', 'HEAD')
        with tarfile.open(archive) as exported:
            for name in launchers:
                with self.subTest(launcher=name):
                    self.assertTrue(exported.getmember(name).mode & 0o111)
                    data = exported.extractfile(name).read()
                    self.assertTrue(data.startswith(b'#!/bin/sh\n'))
                    self.assertNotIn(b'\r', data)

    def test_repeated_creation_preserves_task(self):
        self.run_cli('new', 'refunds')
        plan = self.project / 'docs/work/refunds/plan.json'
        original = plan.read_bytes()
        self.assertNotEqual(0, self.run_cli('new', 'refunds').returncode)
        self.assertEqual(original, plan.read_bytes())

    def test_task_path_cannot_escape(self):
        self.assertNotEqual(0, self.run_cli('new', '../escape').returncode)
        self.assertFalse((self.project / 'docs/escape').exists())

    def test_validation_returns_failure_exit_code(self):
        self.run_cli('new', 'refunds')
        plan = self.project / 'docs/work/refunds/plan.json'
        data = json.loads(plan.read_text())
        data['status'] = 'READY'
        plan.write_text(json.dumps(data))
        self.assertNotEqual(0, self.run_cli('validate', 'refunds').returncode)

    def test_doctor_reports_missing_installation(self):
        result = self.run_cli('doctor', '--host', 'vscode')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('No Riff skill found', result.stdout)

    def test_status_reports_corrupt_record(self):
        self.run_cli('new', 'refunds')
        (self.project / 'docs/work/refunds/plan.json').write_text('{invalid')
        result = self.run_cli('status', '--json')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('error', json.loads(result.stdout)[0])

    @unittest.skipUnless(shutil.which('git'), 'Git executable required')
    def test_git_visibility_round_trip_preserves_files_and_index(self):
        self.git('init', '--quiet')
        exclude = self.project / '.git/info/exclude'
        original = b'# Local rules\r\n/manual-only/'
        exclude.write_bytes(original)
        gitignore = self.project / '.gitignore'
        gitignore.write_bytes(b'/other-ignore/\n')
        records = self.project / 'docs/work/refunds'
        records.mkdir(parents=True)
        plan = records / 'plan.json'
        plan.write_text('{}')
        self.git('add', '-f', '--', 'docs/work/refunds/plan.json')
        before = self.git('ls-files', '--stage').stdout

        local = self.run_cli('configure', '--git', 'local')
        self.assertEqual(0, local.returncode, local.stderr)
        self.assertIn('already tracked', local.stdout)
        local_rules = exclude.read_bytes()
        self.assertEqual(0, self.run_cli('configure', '--git', 'local').returncode)
        self.assertEqual(local_rules, exclude.read_bytes())
        for path in ('.agents/skills/riff/SKILL.md', '.github/skills/riff/SKILL.md',
                     '.claude/skills/engineering-workflow/SKILL.md',
                     '.riff/project.json', 'docs/work/refunds/run.json'):
            with self.subTest(path=path):
                self.assertEqual(0, self.git('check-ignore', '--', path, check=False).returncode)
        self.assertEqual(0, self.git('check-ignore', '--', '.engineering-workflow/project.json', check=False).returncode)
        for path in ('.agents/skills/other/SKILL.md', '.github/workflows/ci.yml', 'docs/guide.md'):
            self.assertEqual(1, self.git('check-ignore', '--', path, check=False).returncode)
        self.assertEqual(before, self.git('ls-files', '--stage').stdout)

        track = self.run_cli('configure', '--git', 'track')
        self.assertEqual(0, track.returncode, track.stderr)
        self.assertEqual(original, exclude.read_bytes())
        self.assertEqual(b'/other-ignore/\n', gitignore.read_bytes())
        self.assertEqual('{}', plan.read_text())
        self.assertEqual(before, self.git('ls-files', '--stage').stdout)
        self.assertEqual(1, self.git('check-ignore', '--', 'docs/work/refunds/run.json', check=False).returncode)

    @unittest.skipUnless(shutil.which('git'), 'Git executable required')
    def test_untrack_stages_only_riff_removals_and_preserves_local_files(self):
        self.git('init', '--quiet')
        riff_paths = (
            '.riff/project.json',
            '.agents/skills/riff/SKILL.md',
            'docs/work/refunds/plan.json',
            'docs/work/refunds/evidence/check [initial].txt',
        )
        other_paths = ('.agents/skills/other/SKILL.md', 'docs/work/team-notes/notes.md')
        for path in (*riff_paths[1:], *other_paths):
            file = self.project / path
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text('Original content')
        self.git('add', '-f', '--', *riff_paths, *other_paths)
        self.git('-c', 'user.name=Riff Test', '-c', 'user.email=riff@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Track test files')
        unrelated = self.project / other_paths[0]
        unrelated.write_text('Changes already staged')
        self.git('add', '--', other_paths[0])
        local_draft = self.project / riff_paths[-1]
        local_draft.write_text('Local edits to keep')
        originals = {path: (self.project / path).read_bytes() for path in (*riff_paths, *other_paths)}

        result = self.run_cli('configure', '--git', 'local', '--untrack')
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('Staged removal of 4', result.stdout)
        self.assertEqual(set(riff_paths), set(self.git(
            'diff', '--cached', '--diff-filter=D', '--name-only').stdout.splitlines()))
        self.assertEqual(other_paths[0], self.git(
            'diff', '--cached', '--diff-filter=M', '--name-only').stdout.strip())
        self.assertEqual(set(other_paths), set(self.git('ls-files').stdout.splitlines()))
        for path, original in originals.items():
            self.assertEqual(original, (self.project / path).read_bytes())
        for path in riff_paths:
            self.assertEqual(0, self.git('check-ignore', '--', path, check=False).returncode)
        result = self.run_cli('configure', '--git', 'local', '--untrack')
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('No tracked Riff files found', result.stdout)

    @unittest.skipUnless(shutil.which('git'), 'Git executable required')
    def test_untrack_protects_content_only_in_the_git_index(self):
        self.git('init', '--quiet')
        path = '.riff/project.json'
        self.git('add', '-f', '--', path)
        self.git('-c', 'user.name=Riff Test', '-c', 'user.email=riff@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Track Riff settings')
        settings = self.project / path
        settings.write_text('{"artifacts_directory":"docs/work","example":"staged"}')
        self.git('add', '--', path)
        settings.write_text('{"artifacts_directory":"docs/work","example":"working copy"}')
        before = self.git('ls-files', '--stage').stdout
        result = self.run_cli('configure', '--git', 'local', '--untrack')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('staged content', result.stderr)
        self.assertEqual(before, self.git('ls-files', '--stage').stdout)
        self.assertIn('working copy', settings.read_text())

    @unittest.skipUnless(shutil.which('git'), 'Git executable required')
    def test_untrack_requires_local_mode_and_effective_exclusions(self):
        rejected = self.run_cli('configure', '--git', 'track', '--untrack')
        self.assertEqual(2, rejected.returncode)
        self.assertIn('--untrack requires --git local', rejected.stderr)
        self.git('init', '--quiet')
        (self.project / '.gitignore').write_text('!/.riff/\n')
        self.git('add', '--', '.riff/project.json')
        before = self.git('ls-files', '--stage').stdout
        result = self.run_cli('configure', '--git', 'local', '--untrack')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Review existing ignore rules', result.stderr)
        self.assertEqual(before, self.git('ls-files', '--stage').stdout)

    @unittest.skipUnless(shutil.which('git'), 'Git executable required')
    def test_git_visibility_scopes_nested_projects_and_escapes_record_paths(self):
        self.git('init', '--quiet')
        nested = self.project / 'apps/site app'
        settings = nested / '.riff'
        settings.mkdir(parents=True)
        (settings / 'project.json').write_text('{"artifacts_directory":"notes/Riff [drafts]"}')
        local = self.run_cli('configure', '--git', 'local', project=nested)
        self.assertEqual(0, local.returncode, local.stderr)
        for path in ('apps/site app/notes/Riff [drafts]/test/run.json',
                     'apps/site app/.agents/skills/riff/SKILL.md'):
            self.assertEqual(0, self.git('check-ignore', '--', path, check=False).returncode)
        for path in ('apps/site app/notes/Riff d/test/run.json', 'notes/Riff [drafts]/test/run.json',
                     '.agents/skills/riff/SKILL.md'):
            self.assertEqual(1, self.git('check-ignore', '--', path, check=False).returncode)
        plan = nested / 'notes/Riff [drafts]/test/plan.md'
        plan.parent.mkdir(parents=True)
        plan.write_text('# Test plan')
        self.git('add', '-f', '--', 'apps/site app/notes/Riff [drafts]/test/plan.md')
        untrack = self.run_cli('configure', '--git', 'local', '--untrack', project=nested)
        self.assertEqual(0, untrack.returncode, untrack.stderr)
        self.assertIn('Staged removal of 1', untrack.stdout)
        self.assertEqual('', self.git('ls-files').stdout)
        self.assertEqual('# Test plan', plan.read_text())

    @unittest.skipUnless(shutil.which('git'), 'Git executable required')
    def test_init_wizard_and_configuration_changes_keep_git_visibility(self):
        self.git('init', '--quiet')
        result = self.run_cli('init', '--host', 'codex', answers='\n' * 6 + 'local\n\n')
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('Git visibility', result.stdout)
        self.assertEqual(0, self.git('check-ignore', '--', '.agents/skills/riff/SKILL.md', check=False).returncode)
        answers = '\n'.join(['', '', 'task history', '', '', '', '', '', ''])
        result = self.run_cli('configure', '--host', 'codex', answers=answers)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(0, self.git('check-ignore', '--', 'task history/refunds/run.json', check=False).returncode)
        self.assertEqual(0, self.git('check-ignore', '--', 'docs/work/refunds/run.json', check=False).returncode)
        result = self.run_cli('configure', '--git', 'track')
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(1, self.git('check-ignore', '--', 'task history/refunds/run.json', check=False).returncode)
        self.assertEqual(1, self.git('check-ignore', '--', 'docs/work/refunds/run.json', check=False).returncode)

    def test_explicit_git_visibility_requires_a_repository(self):
        result = self.run_cli('init', '--host', 'codex', '--git', 'local')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('requires a Git working tree', result.stderr)
        self.assertFalse((self.project / '.agents').exists())

    @unittest.skipUnless(shutil.which('git'), 'Git executable required')
    def test_git_visibility_from_linked_worktree(self):
        self.git('init', '--quiet')
        self.git('-c', 'user.name=Riff Test', '-c', 'user.email=riff@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '--allow-empty', '-qm', 'Baseline')
        linked = self.cwd / 'linked'
        self.git('worktree', 'add', '--quiet', '--detach', str(linked))
        result = self.run_cli('init', '--host', 'codex', '--git', 'local', project=linked, answers='\n' * 7)
        self.assertEqual(0, result.returncode, result.stderr)
        check = self.git('check-ignore', '--', '.agents/skills/riff/SKILL.md', project=linked, check=False)
        self.assertEqual(0, check.returncode, check.stderr)
        self.assertIn('Riff local files', (self.project / '.git/info/exclude').read_text())
        self.assertEqual(0, self.git('check-ignore', '--', '.agents/skills/riff/SKILL.md', check=False).returncode)
        result = self.run_cli('configure', '--git', 'track', project=linked)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue((linked / '.agents/skills/riff/SKILL.md').is_file())
        self.assertNotIn('Riff local files', (self.project / '.git/info/exclude').read_text())


    @unittest.skipUnless(os.name == 'nt', 'Windows command launcher')
    def test_windows_install_and_upgrade(self):
        prefix = self.project / 'Riff install'
        binary = prefix / 'bin' / 'riff.cmd'

        for _ in range(2):
            result = subprocess.run(
                [sys.executable, str(INSTALLER), '--prefix', str(prefix), '--print-bin-path'],
                capture_output=True, text=True, cwd=self.cwd,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            bin_path = result.stdout.strip()
            self.assertEqual(binary.parent.resolve(), Path(bin_path))

        env = dict(os.environ)
        env['PATH'] = os.pathsep.join((bin_path, str(Path(sys.executable).parent), env['PATH']))

        result = subprocess.run(
            ['cmd.exe', '/d', '/c', 'riff', 'new', 'refunds', '--title', 'Partial refunds',
             '--project', str(self.project)],
            capture_output=True, text=True, cwd=self.cwd, env=env,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        plan = json.loads((self.project / 'docs/work/refunds/plan.json').read_text())
        self.assertEqual('Partial refunds', plan['title'])

        result = subprocess.run(
            ['cmd.exe', '/d', '/c', 'riff', 'design', 'Compare refund interfaces',
             '--project', str(self.project)],
            capture_output=True, text=True, cwd=self.cwd, env=env,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('$riff Design', result.stdout)
        self.assertIn('Compare refund interfaces', result.stdout)

        result = subprocess.run(
            ['cmd.exe', '/d', '/c', 'riff', '--invalid-option'],
            capture_output=True, text=True, cwd=self.cwd, env=env,
        )
        self.assertEqual(2, result.returncode, result.stderr)


if __name__ == '__main__':
    unittest.main()
