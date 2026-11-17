import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'routing'))
sys.path.insert(0, str(ROOT / 'routing/tests'))
from adapters import FakeAdapter, capability_report, prepare_request, validate_request, validate_result, reconciliation_proposal
from router import propose
from gates import validate, passed
import test_router


class AdapterTests(unittest.TestCase):
    def inputs(self):
        return test_router.RoutingTests().inputs()

    def request(self):
        inputs = self.inputs()
        return prepare_request(propose(*inputs), *inputs, 'request-1')

    def test_request_binding_and_no_mutation(self):
        inputs = self.inputs()
        before = copy.deepcopy(inputs)
        proposal = propose(*inputs)
        request = prepare_request(proposal, *inputs, 'request-1')
        self.assertEqual(before, inputs)
        self.assertEqual(proposal['snapshot_hash'], request['snapshot_hash'])
        request['assignments'][0]['proposed_model'] = 'forged'
        with self.assertRaisesRegex(ValueError, 'content changed'): validate_request(request)
        self.assertEqual('c', proposal['assignments'][0]['proposed_model'])

    def test_stale_snapshot_and_assignment_rejected(self):
        inputs = self.inputs()
        proposal = propose(*inputs)
        inputs[2]['token_budget'] += 1
        with self.assertRaisesRegex(ValueError, 'stale'): prepare_request(proposal, *inputs, 'new')
        proposal = propose(*inputs)
        proposal['assignments'][0]['token_reservation'] = 1
        with self.assertRaisesRegex(ValueError, 'modified'): prepare_request(proposal, *inputs, 'new')

    def test_missing_accounting_stays_unknown(self):
        self.assertEqual('unknown', capability_report({'models': {}})['accounting'])
        result = FakeAdapter().dispatch(self.request())
        self.assertEqual({'accounting': 'unavailable', 'tokens': None}, result['usage'])
        self.assertTrue(result['simulated'])
        self.assertTrue(all(x['actual_model'] is None and x['agent_id'] is None for x in result['outcomes']))

    def test_result_binding_identity_and_snapshot(self):
        request = self.request()
        result = FakeAdapter().dispatch(request)
        for field in ('request_id', 'snapshot_hash', 'request_digest'):
            changed = copy.deepcopy(result)
            changed[field] = 'stale'
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'does not match'):
                validate_result(changed, request)

    def test_unknown_cannot_automatically_retry(self):
        adapter = FakeAdapter()
        request = self.request()
        result = adapter.dispatch(request, 'unknown')
        self.assertFalse(reconciliation_proposal(result, request)['retry_allowed'])
        with self.assertRaisesRegex(ValueError, 'already observed'): adapter.dispatch(request)
        inputs = self.inputs()
        changed_id = prepare_request(propose(*inputs), *inputs, 'different-id')
        with self.assertRaisesRegex(ValueError, 'already observed'): adapter.dispatch(changed_id)

    def test_simulated_evidence_cannot_qualify_real_execution(self):
        plan, run, _, _ = self.inputs()
        result = FakeAdapter().dispatch(self.request())
        run['dispatch_result'] = result
        self.assertIn('Simulated evidence cannot qualify for execution', validate(plan, run))
        bundle = {'checks': [{'revision': 'abc', 'exit_code': 0, 'command': 'test', 'evidence': 'test.log'}],
                  'reviews': [{'revision': 'abc', 'verdict': 'pass', 'reviewer': 'other',
                               'independent': True, 'kind': 'spec', 'evidence': 'review.md'}],
                  'adapter': result}
        self.assertFalse(passed(bundle, 'abc', 'author', True, ['spec']))

    def test_simulation_cannot_invent_actual_models_or_usage(self):
        request = self.request()
        result = FakeAdapter().dispatch(request)
        result['outcomes'][0]['actual_model'] = 'c'
        with self.assertRaisesRegex(ValueError, 'invent actual'): validate_result(result, request)
        result['outcomes'][0]['actual_model'] = None
        result['usage'] = {'accounting': 'available', 'tokens': 0}
        with self.assertRaisesRegex(ValueError, 'actual usage'): validate_result(result, request)

    def test_failure_reconciliation_does_not_reset_state(self):
        request = self.request()
        result = FakeAdapter().dispatch(request, 'failed')
        before = copy.deepcopy(result)
        proposal = reconciliation_proposal(result, request)
        self.assertEqual(before, result)
        self.assertFalse(proposal['retry_allowed'])
        self.assertIn('coordinator', proposal['next_action'])

    def test_strict_capability_types(self):
        for host in ({'available_slots': True}, {'parallel_agents': 'yes'}, {'models': {'m': 'coding'}},
                     {'models': {'m': ['unknown']}}, {'accounting': 'free'}):
            with self.subTest(host=host), self.assertRaises(ValueError): capability_report(host)

    def test_bad_result_shapes_fail_clearly(self):
        request = self.request()
        result = FakeAdapter().dispatch(request)
        for key, value in (('simulated', 1), ('outcomes', {}), ('usage', None), ('status', 'complete')):
            changed = copy.deepcopy(result)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): validate_result(changed, request)


if __name__ == '__main__': unittest.main()
