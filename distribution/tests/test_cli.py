import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / 'riff.py'


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        settings = self.project / '.engineering-workflow'
        settings.mkdir()
        (settings / 'project.json').write_text('{"artifacts_directory":"docs/work"}')

    def run_cli(self, *arguments):
        return subprocess.run([sys.executable, str(CLI), *arguments,
                               '--project', str(self.project)],
                              capture_output=True, text=True, cwd='/tmp')

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


if __name__ == '__main__':
    unittest.main()
