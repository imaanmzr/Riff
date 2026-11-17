"""Host-adapter contracts and an explicitly simulated in-memory adapter.

No provider SDK, process launch, reservation or execution-state mutation occurs.
Result validation checks record consistency, not the truth of a host's claims.
"""
import copy
import hashlib
import json
import re

from router import propose, scopes

HASH = re.compile(r'^[a-f0-9]{64}$')
IDENTITY = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$')
CAPABILITIES = {'fast', 'coding', 'deep_reasoning'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def capability_report(host):
    """Copy actual supplied capabilities; absent accounting remains unknown."""
    if not isinstance(host, dict): raise ValueError('Host capabilities must be an object')
    models = host.get('models', {})
    if not isinstance(models, dict): raise ValueError('Host models must be an object')
    for name, supported in models.items():
        if not isinstance(name, str) or not name.strip(): raise ValueError('Invalid host model ID')
        if not isinstance(supported, list) or not supported or any(not isinstance(x, str) or x not in CAPABILITIES for x in supported):
            raise ValueError('Invalid model capabilities: ' + name)
        if len(supported) != len(set(supported)): raise ValueError('Duplicate model capabilities')
    slots = host.get('available_slots', 0)
    if type(slots) is not int or slots < 0: raise ValueError('available_slots must be nonnegative')
    for name in ('parallel_agents', 'isolated_workspaces'):
        if name in host and type(host[name]) is not bool: raise ValueError(name + ' must be boolean')
    accounting = host.get('accounting', 'unknown')
    if accounting not in ('available', 'unavailable', 'unknown'): raise ValueError('Invalid accounting availability')
    return dict(models=copy.deepcopy(models), available_slots=slots,
                parallel_agents=host.get('parallel_agents', False),
                isolated_workspaces=host.get('isolated_workspaces', False), accounting=accounting)


def prepare_request(proposal, plan, run, config, host, request_id, context=None):
    """Bind a current valid routing proposal to immutable request inputs.

    The coordinator must still reserve resources and reconcile before a real
    dispatch. This function neither reserves nor calls any host.
    """
    if not isinstance(request_id, str) or not IDENTITY.fullmatch(request_id):
        raise ValueError('Invalid request identity')
    capabilities = capability_report(host)
    if not isinstance(proposal, dict): raise ValueError('Proposal must be an object')
    expected = propose(plan, run, config, host, context=context)
    if expected.get('errors'): raise ValueError('Current routing gates failed: ' + '; '.join(expected['errors']))
    if proposal != expected: raise ValueError('Proposal is stale or assignments were modified')
    if not expected['assignments']: raise ValueError('Proposal contains no eligible assignments')
    request = dict(schema_version=1, request_id=request_id, snapshot_hash=expected['snapshot_hash'],
                   source_revision=plan.get('source_revision'), head_revision=run.get('head_revision'),
                   plan_revision=plan.get('revision'), plan_digest=digest(plan), run_digest=digest(run),
                   config_digest=digest(config), host_digest=digest(host),
                   assignments=copy.deepcopy(expected['assignments']), capabilities=capabilities)
    request['request_digest'] = digest(request)
    validate_request(request)
    return request


def validate_request(request):
    if not isinstance(request, dict) or type(request.get('schema_version')) is not int or request['schema_version'] != 1:
        raise ValueError('Unsupported adapter request')
    if not isinstance(request.get('request_id'), str) or not IDENTITY.fullmatch(request['request_id']):
        raise ValueError('Invalid request identity')
    for field in ('snapshot_hash', 'plan_digest', 'run_digest', 'config_digest', 'host_digest', 'request_digest'):
        if not isinstance(request.get(field), str) or not HASH.fullmatch(request[field]):
            raise ValueError('Invalid request binding: ' + field)
    if request['request_digest'] != digest({k: v for k, v in request.items() if k != 'request_digest'}):
        raise ValueError('Request content changed')
    if type(request.get('plan_revision')) is not int or request['plan_revision'] < 1:
        raise ValueError('Invalid plan revision')
    if not isinstance(request.get('source_revision'), str) or not request['source_revision']:
        raise ValueError('Missing source baseline')
    if request.get('head_revision') is not None and (not isinstance(request['head_revision'], str) or not request['head_revision']):
        raise ValueError('Invalid execution head revision')
    capabilities = capability_report(request.get('capabilities'))
    assignments = request.get('assignments')
    if not isinstance(assignments, list) or not assignments: raise ValueError('Assignments required')
    seen = set()
    for item in assignments:
        if not isinstance(item, dict): raise ValueError('Assignment must be an object')
        task = item.get('task')
        if not isinstance(task, str) or not task or task in seen: raise ValueError('Invalid or duplicate assignment')
        seen.add(task)
        for field in ('attempt', 'token_reservation'):
            if type(item.get(field)) is not int or item[field] < 1: raise ValueError('Invalid ' + field)
        for field in ('requested_profile', 'selected_profile'):
            if not isinstance(item.get(field), str) or item[field] not in CAPABILITIES:
                raise ValueError('Invalid ' + field)
        ordered = ('fast', 'coding', 'deep_reasoning')
        if ordered.index(item['selected_profile']) < ordered.index(item['requested_profile']):
            raise ValueError('Selected capability must not downgrade requested capability')
        paths = item.get('write_paths')
        if not isinstance(paths, list) or not paths:
            raise ValueError('Explicit assignment write scope required')
        scopes(item)
        model = item.get('proposed_model')
        if not isinstance(model, str) or item['selected_profile'] not in capabilities['models'].get(model, []):
            raise ValueError('Requested model capability unavailable')
    return None


def validate_result(result, request):
    """Validate an outcome record; accepted never means implemented or reviewed."""
    validate_request(request)
    if not isinstance(result, dict) or type(result.get('schema_version')) is not int or result['schema_version'] != 1:
        raise ValueError('Unsupported adapter result')
    for field in ('request_id', 'snapshot_hash', 'request_digest'):
        if result.get(field) != request[field]: raise ValueError('Result does not match request: ' + field)
    if type(result.get('simulated')) is not bool: raise ValueError('Result must explicitly identify simulation')
    if result.get('status') not in ('accepted', 'failed', 'unknown'): raise ValueError('Invalid dispatch outcome')
    outcomes = result.get('outcomes')
    if not isinstance(outcomes, list) or len(outcomes) != len(request['assignments']):
        raise ValueError('Result task set differs from request')
    expected = {a['task']: a for a in request['assignments']}
    seen = set()
    for outcome in outcomes:
        if not isinstance(outcome, dict): raise ValueError('Outcome must be an object')
        task = outcome.get('task')
        if not isinstance(task, str) or task not in expected or task in seen: raise ValueError('Unexpected result task')
        seen.add(task)
        if outcome.get('requested_model') != expected[task]['proposed_model']:
            raise ValueError('Requested model changed')
        for name in ('actual_model', 'agent_id'):
            if name not in outcome: raise ValueError('Explicit actual identity required: ' + name)
            value = outcome.get(name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError('Invalid actual identity: ' + name)
            if result['simulated'] and value is not None: raise ValueError('Simulation cannot invent actual host identities')
            if not result['simulated'] and result['status'] == 'accepted' and value is None:
                raise ValueError('Accepted real outcome needs actual host identities')
        if not result['simulated'] and result['status'] == 'accepted':
            if expected[task]['selected_profile'] not in request['capabilities']['models'].get(outcome['actual_model'], []):
                raise ValueError('Actual model lacks verified required capability')
    usage = result.get('usage')
    if not isinstance(usage, dict) or usage.get('accounting') not in ('available', 'unavailable', 'unknown'):
        raise ValueError('Explicit usage availability required')
    if 'tokens' not in usage: raise ValueError('Explicit tokens value or null required')
    tokens = usage.get('tokens')
    if usage['accounting'] == 'available':
        if type(tokens) is not int or tokens < 0: raise ValueError('Available usage requires actual nonnegative tokens')
    elif tokens is not None:
        raise ValueError('Unavailable accounting must not invent usage')
    if result['simulated'] and (usage['accounting'] != 'unavailable' or tokens is not None):
        raise ValueError('Simulation cannot claim actual usage')
    return None


def reconciliation_proposal(result, request):
    validate_result(result, request)
    status = result['status']
    return dict(request_id=request['request_id'], snapshot_hash=request['snapshot_hash'],
                simulated=result['simulated'], status=status, retry_allowed=False,
                next_action=('Inspect host and workspace; retain reservation until outcome is known'
                             if status == 'unknown' else
                             'Record failure evidence; coordinator must resolve before another attempt'
                             if status == 'failed' else
                             'Simulated acceptance only; no real task transition is permitted'
                             if result['simulated'] else
                             'Reconcile actual host identity; acceptance is not implementation completion'))


class FakeAdapter:
    """Deterministic contract exerciser, never a real host or cost estimator."""
    def __init__(self):
        self._attempts = set()
        self._requests = set()

    def dispatch(self, request, outcome='accepted'):
        validate_request(request)
        if outcome not in ('accepted', 'failed', 'unknown'): raise ValueError('Invalid simulated outcome')
        keys = {(item['task'], item['attempt']) for item in request['assignments']}
        if request['request_id'] in self._requests or self._attempts.intersection(keys):
            raise ValueError('Attempt already observed; inspect and reconcile, never blindly redispatch')
        self._requests.add(request['request_id'])
        self._attempts.update(keys)
        result = dict(schema_version=1, request_id=request['request_id'], snapshot_hash=request['snapshot_hash'],
                      request_digest=request['request_digest'], simulated=True, status=outcome,
                      outcomes=[dict(task=a['task'], requested_model=a['proposed_model'], actual_model=None, agent_id=None)
                                for a in request['assignments']],
                      usage={'accounting': 'unavailable', 'tokens': None})
        validate_result(result, request)
        return result
