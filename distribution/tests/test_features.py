"""End-to-end contract checks against the installed reference implementation."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from distribution import core


class Features(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / '.riff').mkdir()
        (self.root / '.riff/project.json').write_text('{}')
        (self.root / 'source.py').write_text('value = 1\n')
        self.cli('new', 'demo', '--title', 'Demo')
        self.task = self.root / 'docs/work/demo'

    def cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / 'riff.py'), *args, '--project', str(self.root)],
                              capture_output=True, text=True, encoding='utf-8', timeout=30)

    def save(self, plan):
        (self.task / 'plan.json').write_text(json.dumps(plan), encoding='utf-8')

    def ready(self):
        p = core.records.load(self.task / 'plan.json')
        p.update(status='READY', source_revision='baseline', unresolved_questions=[], requirements=['R1'],
                 requirement_details=[dict(id='R1', description='Observable behavior', acceptance_checks=['C1'])],
                 acceptance_checks=[dict(id='C1', requirements=['R1'], procedure='Run focused check', expected='Correct value')],
                 tasks=[dict(id='T1', dependencies=[], requirements=['R1'], capability='coding',
                             **{key: 'specified' for key in ('objective', 'inputs', 'scope', 'outputs', 'owner', 'reviewer', 'verification')})],
                 source_manifest={'source.py': hashlib.sha256((self.root / 'source.py').read_bytes()).hexdigest()})
        p['authored_digest'] = core.records.authored_digest(self.task, p)
        p['reviews'] = [dict(revision=p['revision'], source_revision=p['source_revision'], verdict='pass', reviewer='independent-session', independent=True,
                             authored_digest=p['authored_digest'], config_digest=p['config_digest'], plan_digest=core.records.plan_digest(p))]
        self.save(p)
        return p

    def test_new_is_v2_and_missing_freshness_is_visible(self):
        p = core.records.load(self.task / 'plan.json')
        self.assertEqual(2, p['schema_version'])
        result = self.cli('check', 'demo', '--json')
        self.assertEqual(1, result.returncode, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual('unknown', value['checks']['freshness'])
        self.assertTrue(any(i['category'] == 'question' for i in value['issues']))
        self.assertEqual(0, self.cli('validate', 'demo').returncode)

    def test_readiness_live_prose_config_and_source(self):
        self.ready()
        self.assertEqual(0, self.cli('check', 'demo').returncode)
        original = (self.task / 'plan.md').read_bytes()
        (self.task / 'plan.md').write_text('Changed contract')
        self.assertEqual(1, self.cli('check', 'demo').returncode)
        (self.task / 'plan.md').write_bytes(original)
        self.assertEqual(0, self.cli('config', 'set', 'required_checks', '["additional"]') .returncode)
        self.assertEqual(1, self.cli('check', 'demo').returncode)
        self.cli('config', 'set', 'required_checks', '["acceptance", "regression"]')
        (self.root / 'source.py').write_text('changed')
        value = json.loads(self.cli('check', 'demo', '--json').stdout)
        self.assertEqual('fail', value['checks']['freshness'])

    def test_render_graph_and_output_protection(self):
        self.ready()
        before = {p.name: p.read_bytes() for p in self.task.iterdir() if p.is_file()}
        path = self.root / 'readable.md'
        result = self.cli('render', 'demo', '--output', str(path))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('## At a glance', path.read_text(encoding='utf-8'))
        self.assertNotEqual(0, self.cli('render', 'demo', '--output', str(path)).returncode)
        self.assertEqual(0, self.cli('graph', 'demo').returncode)
        self.cli('new', 'other')
        for protected in (self.task / 'plan.md', self.root / 'docs/work/other/plan.json', self.root / 'source.py'):
            original = protected.read_bytes()
            self.assertNotEqual(0, self.cli('render', 'demo', '--output', str(protected), '--overwrite').returncode)
            self.assertEqual(original, protected.read_bytes())
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.task.iterdir() if p.is_file()})

    def test_workflow_prompts_do_not_mutate_and_use_limits(self):
        before = (self.task / 'plan.json').read_bytes()
        for args in [('research', 'Investigate alternatives'), ('research', '--task', 'demo'),
                     ('debug', '--task', 'demo'), ('replan', 'demo', '--reason', 'Changed contract')]:
            result = self.cli(*args)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn('Paste this into your agent chat', result.stdout)
        self.assertEqual(before, (self.task / 'plan.json').read_bytes())
        self.cli('config', 'set', 'debug_command_timeout', '12')
        self.assertIn('12 seconds per command', self.cli('debug', 'Symptom').stdout)
        self.assertIn('4 seconds per command', self.cli('debug', 'Symptom', '--command-timeout', '4').stdout)
        self.assertEqual(2, self.cli('debug', 'Symptom', '--total-timeout', '0').returncode)

    def test_migration_preview_backup_and_legacy_validation(self):
        legacy = dict(route='small', status='DRAFT', revision=1, requirements=[], tasks=[], reviews=[], custom={'preserve': True})
        self.save(legacy)
        before = (self.task / 'plan.json').read_bytes()
        preview = self.cli('migrate', 'demo')
        self.assertEqual(0, preview.returncode, preview.stderr)
        self.assertEqual(before, (self.task / 'plan.json').read_bytes())
        result = json.loads(self.cli('migrate', 'demo', '--apply').stdout)
        self.assertEqual(before, Path(result['backup']).read_bytes())
        self.assertEqual(legacy['custom'], result['plan']['custom'])
        self.assertEqual('DRAFT', result['plan']['status'])

    def test_checkpoint_generation_reconcile_and_diff(self):
        plan = self.ready()
        run = dict(authorized=True, plan_revision=plan['revision'], base_revision=plan['source_revision'],
                   head_revision='baseline', status='running', tasks={'T1': {'state': 'pending'}})
        (self.task / 'run.json').write_text(json.dumps(run))
        manifest = self.root / 'manifest.json'
        manifest.write_text('["source.py"]')
        arguments = ('checkpoint', 'demo', '--manifest', str(manifest), '--expected-generation', '0')
        first = self.cli(*arguments)
        self.assertEqual(0, first.returncode, first.stderr)
        before = (self.task / 'checkpoint.json').read_bytes()
        self.assertNotEqual(0, self.cli(*arguments).returncode)
        self.assertEqual(before, (self.task / 'checkpoint.json').read_bytes())
        diff = self.cli('diff', 'demo', '--against', str(self.task / 'checkpoint.json'))
        self.assertEqual({}, json.loads(diff.stdout)['changed_fields'])
        plan['presentation'] = {'detail': 'concise'}
        self.save(plan)
        proposal = self.cli('reconcile', 'demo', '--manifest', str(manifest))
        self.assertEqual(0, proposal.returncode, proposal.stderr)
        self.assertFalse(json.loads(proposal.stdout)['recovery']['plan_changed'])
        (self.task / 'plan.md').write_text('Changed specification')
        proposal = self.cli('reconcile', 'demo', '--manifest', str(manifest))
        self.assertEqual(0, proposal.returncode, proposal.stderr)
        self.assertEqual('blocked', json.loads(proposal.stdout)['run']['status'])
        self.assertEqual(before, (self.task / 'checkpoint.json').read_bytes())

    def test_profiles_and_configuration_preserve_unknowns(self):
        path = self.root / '.riff/project.json'
        path.write_text('{"custom": {"preserve": true}}')
        self.assertEqual(0, self.cli('config', 'set', 'profile', 'migration').returncode)
        self.assertTrue(json.loads(path.read_text())['custom']['preserve'])
        config = json.loads(self.cli('config', 'show', '--effective').stdout)
        self.assertEqual('migration', config['profile'])
        self.assertIn('rollback', config['behavior']['required_checks'])
        self.assertIn('compatibility, rollout, rollback', self.cli('plan', 'Plan the migration').stdout)
        self.cli('new', 'migration-task')
        self.assertIn('Workflow profile: migration', self.cli('replan', 'migration-task', '--reason', 'New contract').stdout)
        self.assertEqual(0, self.cli('profile', 'show', 'research').returncode)
        self.assertNotEqual(0, self.cli('config', 'set', 'required_checks', 'false').returncode)

    def test_legacy_settings_remain_usable_without_automatic_moves(self):
        current = self.root / '.riff'
        legacy = self.root / '.engineering-workflow'
        current.rename(legacy)
        settings = legacy / 'project.json'
        settings.write_bytes(b'{"artifacts_directory":"notes/tasks","custom":true}')
        self.assertEqual(0, self.cli('new', 'legacy-task').returncode)
        self.assertTrue((self.root / 'notes/tasks/legacy-task/plan.json').is_file())
        self.assertEqual(0, self.cli('plan', '--task', 'legacy-task').returncode)
        self.assertEqual(0, self.cli('validate', 'legacy-task').returncode)
        self.assertEqual(0, self.cli('config', 'set', 'profile', 'refactor').returncode)
        self.assertTrue(json.loads(settings.read_text())['custom'])
        self.assertEqual('refactor', json.loads(self.cli('config', 'show', '--effective').stdout)['profile'])
        self.assertFalse(current.exists())

    def test_duplicate_settings_reject_config_writes(self):
        current = self.root / '.riff/project.json'
        legacy = self.root / '.engineering-workflow/project.json'
        legacy.parent.mkdir()
        legacy.write_bytes(b'{"custom":"legacy"}')
        before = (current.read_bytes(), legacy.read_bytes())
        result = self.cli('config', 'set', 'profile', 'refactor')
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Both .riff and .engineering-workflow', result.stderr)
        self.assertEqual(before, (current.read_bytes(), legacy.read_bytes()))

    def test_exports_protect_current_and_legacy_settings_namespaces(self):
        for active, other in (('.riff', '.engineering-workflow'), ('.engineering-workflow', '.riff')):
            with self.subTest(active=active):
                selected = self.root / active
                if not selected.exists():
                    (self.root / other).rename(selected)
                path = selected / 'project.json'
                before = path.read_bytes()
                result = self.cli('render', 'demo', '--output', str(path), '--overwrite')
                self.assertNotEqual(0, result.returncode)
                self.assertEqual(before, path.read_bytes())
                result = self.cli('render', 'demo', '--output', str(self.root / other), '--overwrite')
                self.assertNotEqual(0, result.returncode)
                self.assertIn('authoritative', result.stderr)
                self.assertFalse((self.root / other).exists())

    def test_routing_uses_selected_settings_and_host_specific_files(self):
        plan = self.ready()
        run = dict(authorized=True, plan_revision=plan['revision'], base_revision=plan['source_revision'],
                   status='running', tasks={'T1': {'state': 'pending'}})
        (self.task / 'run.json').write_text(json.dumps(run))
        for name in ('.riff', '.engineering-workflow'):
            with self.subTest(settings=name):
                settings = self.root / name
                if not settings.exists():
                    (self.root / '.riff').rename(settings)
                (settings / 'hosts').mkdir(exist_ok=True)
                route = json.loads((ROOT / 'routing/config.json').read_text())
                route.update(token_budget=4321, task_token_budget=1000,
                             profiles={'fast':None,'coding':'fixture-model','deep_reasoning':None})
                host = json.loads((ROOT / 'routing/host.example.json').read_text())
                host.update(models={'fixture-model':['coding']},available_slots=1)
                (settings / 'routing-codex.json').write_text(json.dumps(route))
                (settings / 'hosts/codex.json').write_text(json.dumps(host))
                # Invalid shared files ensure host-specific lookup really wins.
                (settings / 'routing.json').write_text('invalid shared routing')
                (settings / 'host.json').write_text('invalid shared host')
                result = self.cli('route', 'demo', '--host', 'codex')
                self.assertEqual(0, result.returncode, result.stderr)
                value = json.loads(result.stdout)
                self.assertEqual('fixture-model', value['assignments'][0]['proposed_model'])
                self.assertEqual(3321, value['remaining_tokens'])
                (settings / 'routing.json').write_text(json.dumps(route))
                (settings / 'host.json').write_text(json.dumps(host))
                (settings / 'routing-codex.json').unlink()
                (settings / 'hosts/codex.json').unlink()
                fallback = self.cli('route', 'demo', '--host', 'codex')
                self.assertEqual(0, fallback.returncode, fallback.stderr)
                self.assertEqual('fixture-model', json.loads(fallback.stdout)['assignments'][0]['proposed_model'])

    def test_gate_router_simulated_and_unbound_context(self):
        p = self.ready()
        run = dict(authorized=True, plan_revision=p['revision'], base_revision=p['source_revision'], status='running', tasks={'T1': {'state': 'pending'}})
        ctx = core.config.context(self.task / 'plan.json', self.root)
        self.assertEqual([], core.gates.validate(p, run, ctx))
        self.assertTrue(core.gates.validate(p, run))
        run['tasks']['T1'].update(state='blocked', reason='Waiting for required fixture')
        (self.task / 'run.json').write_text(json.dumps(run), encoding='utf-8')
        result = self.cli('check', 'demo', '--json')
        self.assertEqual(1, result.returncode, result.stderr)
        evaluation = json.loads(result.stdout)
        self.assertEqual('fail', evaluation['checks']['execution'])
        self.assertTrue(any('Waiting for required fixture' in item['message'] for item in evaluation['issues']))
        run['tasks']['T1']['adapter_result'] = {'simulation': True}
        self.assertTrue(core.gates.validate(p, run, ctx))
        p['reviews'][0]['simulation'] = True
        self.save(p)
        self.assertNotEqual(0, self.cli('check', 'demo').returncode)

    def test_legacy_unrestricted_ids(self):
        plan = dict(route='small', status='DRAFT', tasks=[dict(id='old/task name', dependencies=[])])
        self.assertEqual([], core.records.validate(plan))
        self.assertIn('n0', core.records.generated_sections(plan)['graph'])

    def test_stale_review_category_and_future_schema(self):
        plan = self.ready()
        plan['reviews'][0]['revision'] = 0
        self.save(plan)
        value = json.loads(self.cli('check', 'demo', '--json').stdout)
        self.assertEqual('fail', value['checks']['review'])
        plan['schema_version'] = 99
        self.save(plan)
        self.assertNotEqual(0, self.cli('validate', 'demo').returncode)

    def test_registered_report_is_validated_and_binds_narrative(self):
        plan = self.ready()
        reports = self.task / 'reports'
        reports.mkdir()
        (reports / 'Q1.json').write_text('{"id":"Q1", "kind":"research"}')
        (reports / 'Q1.md').write_text('Unresolved research')
        plan['reports'] = [dict(id='Q1', kind='research', path='reports/Q1.json')]
        plan['reviewed_artifacts'] += ['reports/Q1.json', 'reports/Q1.md']
        plan['authored_digest'] = core.records.authored_digest(self.task, plan)
        plan['reviews'][0].update(authored_digest=plan['authored_digest'], plan_digest=core.records.plan_digest(plan))
        self.save(plan)
        value = json.loads(self.cli('check', 'demo', '--json').stdout)
        self.assertTrue(any('report' in i['message'].lower() for i in value['issues']))
        plan['reports'][0]['narrative'] = 'reports/Q1.json'
        errors = core.records.validate(plan, core.config.context(self.task / 'plan.json', self.root))
        self.assertTrue(any('distinct .json and .md' in error for error in errors))


if __name__ == '__main__': unittest.main()
