import json
import os
from pathlib import Path
import subprocess
import sys
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
        settings = self.project / '.engineering-workflow'
        settings.mkdir()
        (settings / 'project.json').write_text('{"artifacts_directory":"docs/work"}')

    def run_cli(self, *arguments):
        return subprocess.run([sys.executable, str(CLI), *arguments,
                               '--project', str(self.project)],
                              capture_output=True, text=True, cwd=self.cwd)

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
            ['cmd.exe', '/d', '/c', 'riff', '--invalid-option'],
            capture_output=True, text=True, cwd=self.cwd, env=env,
        )
        self.assertEqual(2, result.returncode, result.stderr)


if __name__ == '__main__':
    unittest.main()
