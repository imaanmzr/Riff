"""Standalone and composed elicitation through public CLI boundaries."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ElicitationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='riff elicit ')
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name).resolve()

    def cli(self, *args, project_flag=True):
        return subprocess.run([sys.executable, str(ROOT / 'riff.py'), *args,
                               *(['--project', str(self.project)] if project_flag else [])],
                              cwd=self.project, capture_output=True, text=True, encoding='utf-8',
                              env=dict(os.environ, PYTHONUTF8='1'), timeout=30)

    def snapshot(self):
        return {str(p.relative_to(self.project)): p.read_bytes()
                for p in self.project.rglob('*') if p.is_file()}

    def make_task(self, folder='.riff', records='notes/task records'):
        settings = self.project / folder
        settings.mkdir()
        (settings / 'project.json').write_text(json.dumps({'artifacts_directory': records}))
        self.assertEqual(0, self.cli('new', 'demo').returncode)

    def test_standalone_free_topic_without_setup(self):
        for host in ('codex', 'cursor', 'vscode', 'claude'):
            before = self.snapshot()
            result = self.cli('elicit', 'Offline invoice exports', '--focus', 'retry "policy"\nnext case', '--host', host)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn('$riff' if host == 'codex' else '/riff', result.stdout)
            self.assertIn('Elicitation mode: standalone.', result.stdout)
            self.assertIn('Stop after the interview', result.stdout)
            self.assertIn(json.dumps('retry "policy"\nnext case'), result.stdout)
            self.assertEqual(1, result.stdout.count('Elicitation mode:'))
            self.assertEqual(1, result.stdout.count('Elicitation focus (within this action):'))
            self.assertEqual(before, self.snapshot())
        self.assertEqual(0, self.cli('elicit', 'Current topic', project_flag=False).returncode)
        self.assertFalse((self.project / '.riff').exists())
        self.assertFalse((self.project / 'docs').exists())

    def test_saved_task_and_legacy_alias_match(self):
        self.make_task(folder='.engineering-workflow', records='docs/work')
        before = self.snapshot()
        for host in ('codex', 'cursor', 'vscode', 'claude'):
            for focus in ((), ('--focus', 'T-2 retries')):
                direct = self.cli('elicit', '--task', 'demo', '--host', host, *focus)
                legacy = self.cli('prompt', 'demo', '--action', 'elicit', '--host', host, *focus)
                self.assertEqual(0, direct.returncode, direct.stderr)
                self.assertEqual(0, legacy.returncode, legacy.stderr)
                self.assertEqual(direct.stdout, legacy.stdout)
                self.assertIn(json.dumps(str(self.project / 'docs/work/demo')), direct.stdout)
        self.assertEqual(before, self.snapshot())

    def test_modifier_reaches_all_agent_actions(self):
        self.make_task()
        requests = [('onboard',), ('plan', 'Add exports'), ('plan', '--task', 'demo'),
                    ('design', 'Export contract'), ('documentation', '--task', 'demo'),
                    ('docs', '--task', 'demo'), ('architecture', '--task', 'demo'),
                    ('review', '--task', 'demo'), ('audit', '--task', 'demo'),
                    ('execute', 'demo'), ('resume', 'demo'), ('handoff', 'demo'),
                    ('research', 'Export choices'), ('debug', '--task', 'demo'),
                    ('replan', 'demo', '--reason', 'New recipient')]
        before = self.snapshot()
        for host in ('codex', 'cursor', 'vscode', 'claude'):
            for request in requests:
                with self.subTest(host=host, request=request):
                    normal = self.cli(*request, '--host', host)
                    result = self.cli(*request, '--host', host, '--elicit', '--focus', 'T-2 retry behavior')
                    self.assertEqual(0, normal.returncode, normal.stderr)
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertNotIn('Elicitation mode:', normal.stdout)
                    self.assertTrue(result.stdout.startswith(normal.stdout))
                    self.assertEqual(1, result.stdout.count('Elicitation mode: combined.'))
                    self.assertEqual(1, result.stdout.count('Elicitation focus (within this action):'))
                    self.assertIn('After relevant answers, continue the original action', result.stdout)
                    self.assertIn('existing authorization and gates', result.stdout)
        for operation in ('plan', 'execute', 'resume', 'audit'):
            args = ('--task', 'demo') if operation in ('plan', 'audit') else ('demo',)
            direct = self.cli(operation, *args, '--elicit', '--focus', 'failures')
            legacy = self.cli('prompt', 'demo', '--action', operation, '--elicit', '--focus', 'failures')
            self.assertEqual(direct.stdout, legacy.stdout)
        self.assertEqual(before, self.snapshot())

    def test_invalid_targets_and_modifiers_do_not_write(self):
        self.make_task()
        before = self.snapshot()
        for args in [('elicit',), ('elicit', 'topic', '--task', 'demo'),
                     ('elicit', '--elicit', 'topic'), ('elicit', 'topic', '--focus', ' '),
                     ('elicit', 'topic', '--focus'), ('elicit', 'topic', '--host', 'unknown'),
                     ('onboard', '--focus', 'rules'), ('plan', '--task', 'demo', '--focus', 'rules'),
                     ('prompt', 'demo', '--action', 'plan', '--focus', 'rules'),
                     ('status', '--elicit'), ('check', 'demo', '--elicit'),
                     ('config', 'show', '--focus', 'rules'), ('configure', '--elicit'),
                     ('render', 'demo', '--elicit'), ('new', 'other', '--elicit')]:
            with self.subTest(args=args):
                self.assertEqual(2, self.cli(*args).returncode)
        for args in [('elicit', ''), ('elicit', '--task', 'missing'), ('elicit', '--task', '../escape')]:
            self.assertNotEqual(0, self.cli(*args).returncode)
        self.assertEqual(before, self.snapshot())

    def test_task_discovery_errors_remain_errors(self):
        settings = self.project / '.riff'
        settings.mkdir()
        path = settings / 'project.json'
        for content in ('{invalid', '[]', '{"artifacts_directory":"../outside"}'):
            path.write_text(content)
            before = self.snapshot()
            self.assertNotEqual(0, self.cli('elicit', '--task', 'demo').returncode)
            self.assertEqual(before, self.snapshot())
        path.write_text('{}')
        (self.project / '.engineering-workflow').mkdir()
        self.assertNotEqual(0, self.cli('elicit', '--task', 'demo').returncode)


if __name__ == '__main__':
    unittest.main()
