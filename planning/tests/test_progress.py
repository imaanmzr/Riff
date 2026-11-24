"""Current actions derive from live evaluation and candidate-bound execution records."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from riff_core import progress, presentation


class ProgressTests(unittest.TestCase):
    def fixture(self):
        plan = dict(schema_version=2, task_id='work', title='Useful change', route='critical', status='READY',
                    revision=2, source_revision='baseline', next_action='Implement T1',
                    tasks=[dict(id='T1', objective='First', dependencies=[]),
                           dict(id='T2', objective='Second', dependencies=['T1']),
                           dict(id='T3', objective='Third', dependencies=['T2'])], reviews=[])
        def reviewed(candidate):
            return [dict(kind=k, revision=candidate, reviewer='independent', independent=True,
                         verdict='pass', evidence='actual review') for k in ('spec','quality','invariants')]
        run = dict(status='running', authorized=True, plan_revision=2, base_revision='baseline',
                   tasks={'T1':dict(state='integrated', agent='author', candidate_revision='done',
                                    integration_revision='integrated', reviews=reviewed('done'),
                                    checks=[dict(revision='done', command='tests', exit_code=0, evidence='log')]),
                          'T2':dict(state='review', agent='author', candidate_revision='current', reviews=[],
                                    checks=[dict(revision='current', command='tests', exit_code=0, evidence='log')]),
                          'T3':dict(state='pending', checks=[], reviews=[])})
        evaluation = dict(recorded_status='READY', evaluated_status='READY',
                          checks=dict(structure='pass',review='pass',freshness='pass',execution='pass',readiness='pass'),
                          issues=[], eligible_tasks=[], next_action='Old generic action')
        return plan, run, evaluation

    def summarize(self, plan, run, evaluation):
        return progress.summarize(Path('/project/docs/work/work'), plan, run, evaluation, project=Path('/project'))

    def test_current_review_and_dependency_wait_beat_old_handoff_without_mutation(self):
        plan, run, evaluation = self.fixture()
        before = copy.deepcopy((plan,run,evaluation))
        item = self.summarize(plan,run,evaluation)
        self.assertEqual('review',item['phase'])
        self.assertIn('T2',item['next_action'])
        self.assertEqual(['spec','quality','invariants'],item['tasks'][1]['reviews']['missing_kinds'])
        self.assertEqual(['T2'],item['tasks'][2]['waiting_for'])
        self.assertEqual(['riff','resume','work','--project',str(Path('/project'))],item['next_command_argv'])
        self.assertEqual(before,(plan,run,evaluation))

    def test_legacy_recorded_ready_suggests_migration_and_never_dispatch(self):
        plan,run,evaluation=self.fixture();plan.pop('schema_version')
        evaluation.update(evaluated_status='BLOCKED',eligible_tasks=['T3'])
        evaluation['checks']['freshness']='unknown'
        item=self.summarize(plan,run,evaluation)
        self.assertEqual('migration',item['phase'])
        self.assertEqual(['riff','migrate','work'],item['next_command_argv'][:3])
        self.assertFalse(any(t['eligible'] for t in item['tasks']))

    def test_stale_rejections_are_history_but_current_rejections_request_rework(self):
        plan,run,evaluation=self.fixture()
        record=run['tasks']['T2'];record['state']='running'
        record['reviews']=[dict(kind='spec',revision='old',verdict='changes-required')]
        item=self.summarize(plan,run,evaluation)
        self.assertEqual([],item['tasks'][1]['reviews']['current'])
        self.assertEqual(1,len(item['tasks'][1]['reviews']['historical']))
        record['reviews'].append(dict(kind='invariants',revision='current',verdict='changes-required'))
        self.assertIn('Address current invariants',self.summarize(plan,run,evaluation)['next_action'])

    def test_missing_check_evidence_cannot_suggest_integration(self):
        plan,run,evaluation=self.fixture()
        run['tasks']['T2']['checks'][0].pop('evidence')
        item=self.summarize(plan,run,evaluation)
        self.assertEqual(0,item['tasks'][1]['checks']['passed'])
        self.assertEqual(1,item['tasks'][1]['checks']['unknown'])
        self.assertIn('Complete the current check',item['next_action'])

    def test_complete_claim_with_failed_evaluation_remains_reconciliation(self):
        plan,run,evaluation=self.fixture();run['status']='complete'
        evaluation.update(evaluated_status='BLOCKED',next_action='Missing final integrated review')
        evaluation['checks']['execution']='fail'
        item=self.summarize(plan,run,evaluation)
        self.assertEqual('reconciliation',item['phase'])
        self.assertIn('Missing final',item['next_action'])

    def test_generated_handoff_uses_same_current_action_and_keeps_authored_prose(self):
        plan,run,evaluation=self.fixture();current=self.summarize(plan,run,evaluation)
        report=dict(evaluation,next_action=current['next_action'],progress=current)
        authored='Next action: Implement T1. This is the original reviewed specification.'
        text=presentation.render_markdown(plan,authored,report,diagrams='none')
        self.assertIn('**Next action:** '+current['next_action'],text)
        self.assertIn('Current phase: review',text)
        self.assertIn(authored,text)

    def test_blocked_plan_without_run_cannot_recommend_execution(self):
        plan,_,evaluation=self.fixture()
        plan['blockers']=['Unresolved risk policy']
        evaluation.update(evaluated_status='BLOCKED',next_action='Resolve policy')
        item=self.summarize(plan,{},evaluation)
        self.assertEqual('planning',item['phase'])
        self.assertNotIn('execute',item['next_command_argv'])

    def test_otherwise_ready_plan_requests_authorization_but_recovery_blockers_win(self):
        plan,run,evaluation=self.fixture()
        item=self.summarize(plan,{},evaluation)
        self.assertEqual('authorization',item['phase'])
        self.assertIn('execute',item['next_command_argv'])
        run['authorized']=False
        evaluation.update(evaluated_status='BLOCKED',next_action='Reconcile interrupted execution',
                          issues=[dict(category='execution',message='Recovery reconciliation required')])
        item=self.summarize(plan,run,evaluation)
        self.assertEqual('reconciliation',item['phase'])
        self.assertNotIn('execute',item['next_command_argv'])

    def test_failed_freshness_gates_task_and_current_work_in_every_handoff(self):
        plan,run,evaluation=self.fixture()
        run['tasks']['T2']['reviews']=[dict(kind=k,revision='current',verdict='pass',reviewer='independent',
                                          independent=True,evidence='review') for k in ('spec','quality','invariants')]
        evaluation.update(evaluated_status='BLOCKED',next_action='Reconcile source drift')
        evaluation['checks']['freshness']='fail'
        item=self.summarize(plan,run,evaluation)
        for action in (item['tasks'][1]['next_action'],item['current_work']['next_action']):
            self.assertNotIn('integrate',action.lower())
            self.assertIn('gates',action)
        text=presentation.render_markdown(plan,'# Original specification',dict(evaluation,progress=item),diagrams='none')
        self.assertNotIn('integrate the reviewed candidate',text)
        evaluation.update(evaluated_status='READY')
        evaluation['checks']['freshness']='pass'
        self.assertIn('integrate the reviewed candidate',self.summarize(plan,run,evaluation)['tasks'][1]['next_action'])


if __name__ == '__main__':
    unittest.main()
