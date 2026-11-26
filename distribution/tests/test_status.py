"""Read-only status behavior at the real CLI boundary."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class StatusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        (self.project / '.riff').mkdir()
        (self.project / '.riff/project.json').write_text('{}')
        self.task = self.project / 'docs/riff/storage'
        self.task.mkdir(parents=True)

    def cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / 'riff.py'), 'status', *args,
                               '--project', str(self.project)], capture_output=True,
                              text=True, encoding='utf-8', timeout=30)

    def write(self, name, value):
        (self.task / name).write_text(json.dumps(value), encoding='utf-8')

    def running_fixture(self):
        plan = dict(id='storage', title='Storage authority', route='critical', status='READY',
                    revision=2, source_revision='base', requirements=['R1'],
                    tasks=[dict(id=f'T{i}', objective=f'Operation {i}', requirements=['R1'],
                                dependencies=[] if i == 1 else [f'T{i-1}']) for i in range(1, 4)],
                    reviews=[dict(revision=1, source_revision='base', verdict='pass', reviewer='old', independent=True),
                             dict(revision=2, source_revision='base', verdict='pass', reviewer='planner', independent=True)])
        def reviews(candidate, verdict):
            return [dict(kind=kind, revision=candidate, verdict=verdict, reviewer='reviewer',
                         independent=True, evidence='review evidence') for kind in ('spec', 'quality', 'invariants')]
        run = dict(authorized=True, plan_revision=2, base_revision='base', head_revision='base',
                   status='running', tasks={
                       'T1': dict(state='integrated', agent='author', candidate_revision='done',
                                  integration_revision='done', checks=[dict(revision='done', command='test', evidence='log', exit_code=0)],
                                  reviews=reviews('done', 'pass')),
                       'T2': dict(state='running', agent='author', candidate_revision='fixed',
                                  checks=[dict(revision='fixed', command='regression', evidence='log', exit_code=0)],
                                  reviews=reviews('before-fix', 'changes-required')),
                       'T3': dict(state='pending', checks=[], reviews=[])})
        self.write('plan.json', plan); self.write('run.json', run)
        return plan, run

    def test_default_status_explains_progress_reviews_and_next_work_without_mutation(self):
        self.running_fixture()
        before = {p.name: p.read_bytes() for p in self.task.iterdir()}
        result = self.cli()
        self.assertEqual(0, result.returncode, result.stderr)
        for expected in ('Storage authority', '1/3 integrated', 'T2', 'historical', 'changes-required',
                         'spec', 'quality', 'invariants', 'T3', 'Next:'):
            self.assertIn(expected, result.stdout)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.task.iterdir()})

    def test_json_separates_current_candidate_reviews_from_historical_changes_required(self):
        self.running_fixture()
        result = self.cli('storage', '--json')
        self.assertEqual(0, result.returncode, result.stderr)
        item = json.loads(result.stdout)[0]
        self.assertEqual('READY', item['plan_status'])  # Existing JSON keys remain.
        self.assertEqual('running', item['execution_status'])
        self.assertEqual(1, item['progress']['integrated'])
        current = next(t for t in item['tasks'] if t['id'] == 'T2')
        self.assertEqual([], current['reviews']['current'])
        self.assertEqual(3, len(current['reviews']['historical']))
        self.assertEqual(['spec', 'quality', 'invariants'], current['reviews']['missing_kinds'])
        self.assertEqual(['T2'], next(t for t in item['tasks'] if t['id'] == 'T3')['waiting_for'])
        self.assertEqual('unknown', item['evaluation']['checks']['freshness'])

    def test_status_checks_live_inputs_and_does_not_turn_recorded_ready_into_verified_readiness(self):
        self.running_fixture()
        plan = json.loads((self.task / 'plan.json').read_text())
        plan.update(schema_version=2, source_manifest={'source.py': hashlib.sha256(b'old').hexdigest()},
                    reviewed_artifacts=['plan.md'])
        self.write('plan.json', plan)
        (self.task / 'plan.md').write_text('Plan')
        (self.project / 'source.py').write_text('changed')
        result = self.cli('--json')
        item = json.loads(result.stdout)[0]
        self.assertEqual('READY', item['plan_status'])
        self.assertEqual('BLOCKED', item['evaluation']['evaluated_status'])
        self.assertEqual('fail', item['evaluation']['checks']['freshness'])

    def test_missing_run_unbound_evidence_parent_and_external_prerequisites_are_visible(self):
        plan, _ = self.running_fixture()
        (self.task / 'run.json').unlink()
        plan.update(parent='docs/riff/v1', next_action='Review the storage contract.',
                    external_prerequisites=[dict(id='REFERENCE', status='unresolved', affects=['T3'], requirement='Reference machine access')])
        self.write('plan.json', plan)
        item = json.loads(self.cli('--json').stdout)[0]
        self.assertEqual('not started', item['execution_status'])
        self.assertEqual('docs/riff/v1', item['parent'])
        self.assertEqual('Reference machine access', item['external_prerequisites'][0]['requirement'])
        self.assertEqual(3, item['progress']['not started'])
        self.assertTrue(item['next_action'])

    def test_corrupt_neighbor_does_not_hide_healthy_plan(self):
        self.running_fixture()
        bad = self.task.parent / 'broken'; bad.mkdir()
        (bad / 'plan.json').write_text('{broken')
        result = self.cli('--json')
        self.assertEqual(1, result.returncode)
        items = {i['task']: i for i in json.loads(result.stdout)}
        self.assertIn('error', items['broken'])
        self.assertEqual(3, items['storage']['progress']['total'])


if __name__ == '__main__':
    unittest.main()
