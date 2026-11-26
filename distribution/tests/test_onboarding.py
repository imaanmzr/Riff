"""Public onboarding prompts and ownership boundaries in real temporary projects."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from distribution import core


class OnboardingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='riff onboarding ')
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name).resolve()

    def cli(self, *args, project_flag=True):
        return subprocess.run([sys.executable, str(ROOT / 'riff.py'), *args,
                               *(['--project', str(self.project)] if project_flag else [])],
                              cwd=self.project, capture_output=True, text=True,
                              encoding='utf-8', env=dict(os.environ, PYTHONUTF8='1'), timeout=30)

    def snapshot(self):
        return {p.relative_to(self.project): p.read_bytes()
                for p in self.project.rglob('*') if p.is_file()}

    def settings(self, value, directory='.riff'):
        path = self.project / directory / 'project.json'
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')
        return path

    def test_prompts_read_only_with_or_without_settings(self):
        for settings, directory, records in ((None, '.riff', 'docs/riff'),
                                              ({}, '.riff', 'docs/riff'),
                                              ({'artifacts_directory': 'notes/work space'}, '.riff', 'notes/work space'),
                                              ({'artifacts_directory': 'docs/work'}, '.engineering-workflow', 'docs/work')):
            for name in ('.riff', '.engineering-workflow'):
                shutil.rmtree(self.project / name, ignore_errors=True)
            if settings is not None:
                self.settings(settings, directory)
            before = self.snapshot()
            for host in ('codex', 'cursor', 'vscode', 'claude'):
                result = self.cli('onboard', '--host', host)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertIn('$riff' if host == 'codex' else '/riff', result.stdout)
                self.assertIn(json.dumps(str(self.project / records / 'project.md')), result.stdout)
                self.assertIn('do not run project commands', result.stdout)
            self.assertEqual(before, self.snapshot())
        self.assertEqual(0, self.cli('onboard', project_flag=False).returncode)
        self.assertNotEqual(0, self.cli('onboard', 'some-task').returncode)
        self.assertNotEqual(0, self.cli('onboard', '--task', 'some-task').returncode)
        self.assertNotEqual(0, self.cli('onboard', '--host', 'unknown').returncode)

    def test_configuration_errors_do_not_fall_back(self):
        path = self.settings({})
        for content in ('{invalid', '[]', '{"artifacts_directory":"../escape"}',
                        '{"artifacts_directory":"."}', '{"artifacts_directory":null}'):
            path.write_text(content)
            before = self.snapshot()
            self.assertNotEqual(0, self.cli('onboard').returncode)
            self.assertEqual(before, self.snapshot())
        path.write_text('{}')
        self.settings({}, '.engineering-workflow')
        self.assertNotEqual(0, self.cli('onboard').returncode)

    def test_status_ignores_root_guide_and_binding_is_explicit(self):
        self.settings({})
        self.assertEqual(0, self.cli('new', 'demo').returncode)
        task = self.project / 'docs/riff/demo'
        plan = core.records.load(task / 'plan.json')
        guide = self.project / 'docs/riff/project.md'
        original_digest = core.records.authored_digest(task, plan)
        guide.write_text('First draft')
        guide.write_text('Updated context')
        self.assertEqual(original_digest, core.records.authored_digest(task, plan))
        self.assertEqual(['demo'], [x['task'] for x in json.loads(self.cli('status', '--json').stdout)])
        plan['reviewed_artifacts'].append('../project.md')
        # Explicit authored paths use the existing task-relative contract (no traversal).
        with self.assertRaises(ValueError):
            core.records.authored_digest(task, plan)
        context = dict(project=self.project, task_dir=task, effective_behavior=plan['behavior_config'])
        import hashlib
        plan['reviewed_artifacts'] = ['plan.md']
        plan['source_manifest'] = {'docs/riff/project.md': hashlib.sha256(guide.read_bytes()).hexdigest()}
        self.assertFalse(any('Source changed' in e for e in core.records.live_errors(plan, context)))
        guide.write_text('Changed bound evidence')
        self.assertTrue(any('Source changed' in e for e in core.records.live_errors(plan, context)))

    @unittest.skipUnless(shutil.which('git'), 'Git required')
    def test_untrack_only_owned_root_guide(self):
        def git(*args):
            return subprocess.run(['git', '-C', str(self.project), *args],
                                  check=True, capture_output=True).stdout
        git('init')
        self.settings({})
        records = self.project / 'docs/riff'
        records.mkdir(parents=True)
        guide = records / 'project.md'
        other = records / 'notes.md'
        other.write_text('Keep tracked')
        for content in (b'Human-authored guide\n', b'<!-- riff:onboard -->\nmissing end\n',
                        b'<!-- /riff:onboard -->\n<!-- riff:onboard -->\n',
                        b'<!-- riff:onboard -->\n<!-- riff:onboard -->\n<!-- /riff:onboard -->\n',
                        b'prefix <!-- riff:onboard -->\n<!-- /riff:onboard -->\n',
                        b'Notes\n<!-- riff:onboard -->\r\nManaged\r\n<!-- /riff:onboard -->\n'):
            guide.write_bytes(content)
            git('add', '-f', '--', 'docs/riff/project.md', 'docs/riff/notes.md')
            before = self.snapshot()
            self.assertEqual(0, self.cli('onboard').returncode)
            self.assertEqual(before, self.snapshot())
            result = self.cli('configure', '--git', 'local', '--untrack')
            self.assertEqual(0, result.returncode, result.stderr)
            owned = content.startswith(b'Notes')
            tracked = git('ls-files').decode().splitlines()
            self.assertEqual(not owned, 'docs/riff/project.md' in tracked)
            self.assertIn('docs/riff/notes.md', tracked)
            self.assertEqual(content, guide.read_bytes())
            if not owned:
                self.assertIn('Skipped project guide', result.stdout)

    def test_symlink_is_never_owned(self):
        target = self.project / 'target.md'
        target.write_bytes(b'<!-- riff:onboard -->\nManaged\n<!-- /riff:onboard -->\n')
        link = self.project / 'project.md'
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest('Symlink creation unavailable')
        self.assertFalse(core.onboarding.owned_guide(link))


if __name__ == '__main__':
    unittest.main()
