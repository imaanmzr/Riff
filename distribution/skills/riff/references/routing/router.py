"""Deterministic dispatch proposals. Does not invoke providers or reserve resources."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'execution'))
from gates import validate, ready
from riff_core.config import context as live_context

PROFILES = ('fast', 'coding', 'deep_reasoning')


def integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(name + ' must be an integer >= ' + str(minimum))
    return value


def scopes(task):
    values = task.get('write_paths')
    if not values: return ['.']  # Unknown scope takes exclusive ownership.
    if not isinstance(values, list): raise ValueError('write_paths must be an array')
    result = []
    for value in values:
        if not isinstance(value, str) or not value or '\\' in value or any(c in value for c in '*?['):
            raise ValueError('Use literal relative write paths')
        p = PurePosixPath(value)
        if p.is_absolute() or '..' in p.parts: raise ValueError('Unsafe write path')
        result.append(str(p))
    return result


def overlaps(left, right):
    return any(a == '.' or b == '.' or a == b or a.startswith(b + '/') or b.startswith(a + '/')
               for a in left for b in right)


def propose(plan, run, config, host, context=None):
    errors = validate(plan, run, context)
    if errors: return {'errors': errors, 'assignments': [], 'deferred': {}}
    cap = integer(config['max_parallel'], 'max_parallel', 1)
    if host.get('parallel_agents') is not True: cap = 1
    if host.get('isolated_workspaces') is not True: cap = 1
    cap = min(cap, integer(host['available_slots'], 'available_slots'))
    limit = integer(config['token_budget'], 'token_budget')
    attempts_limit = integer(config['max_attempts'], 'max_attempts', 1)
    usage = run.get('routing', {})
    spent = integer(usage.get('spent_tokens', 0), 'spent_tokens')
    records = run['tasks']
    tasks = {t['id']: t for t in plan['tasks']}
    active = [tid for tid,r in records.items() if r['state'] in ('running','review')]
    reserved = 0
    occupied = []
    for tid in active:
        occupied.append(scopes(tasks[tid]))
        # Missing reservation means budget safety cannot be established.
        reserved += integer(records[tid]['routing']['reserved_tokens'], 'reserved_tokens', 1)
    remaining = max(0, limit - spent - reserved)
    slots = max(0, cap - len(active))
    output = {'errors': [], 'assignments': [], 'deferred': {}, 'remaining_tokens': remaining}
    eligible = ready(plan, run, context)
    for tid in eligible:
        task, record = tasks[tid], records[tid]
        attempt = integer(record.get('routing', {}).get('attempts', 0), 'attempts')
        if attempt >= attempts_limit:
            output['deferred'][tid] = 'Attempt limit; resolve failure or revise budget explicitly'; continue
        requested = task.get('capability', 'coding')
        if requested not in PROFILES: raise ValueError('Unknown capability: ' + str(requested))
        # Recorded failure escalates capability, never automatically retries work.
        floor = PROFILES.index(requested)
        if attempt or plan['route'] == 'critical': floor = max(floor, 2)
        model = None
        chosen = None
        for profile in PROFILES[floor:]:
            candidate = config['profiles'].get(profile)
            if candidate and candidate in host['models'] and profile in host['models'][candidate]:
                model, chosen = candidate, profile; break
        if model is None:
            output['deferred'][tid] = 'No available model satisfies capability'; continue
        budget = integer(task.get('token_budget', config['task_token_budget']), 'task_token_budget', 1)
        paths = scopes(task)
        if not slots: output['deferred'][tid] = 'Concurrency limit'; continue
        if any(overlaps(paths, other) for other in occupied):
            output['deferred'][tid] = 'Write scope overlaps active or selected task'; continue
        if budget > remaining: output['deferred'][tid] = 'Insufficient unreserved token budget'; continue
        output['assignments'].append(dict(task=tid, requested_profile=requested,
            selected_profile=chosen, proposed_model=model, attempt=attempt+1,
            token_reservation=budget, write_paths=paths))
        occupied.append(paths); slots -= 1; remaining -= budget
    output['remaining_tokens'] = remaining
    output['snapshot_hash'] = hashlib.sha256(json.dumps([plan,run,config,host],sort_keys=True).encode()).hexdigest()
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('plan','run','config','host'): parser.add_argument('--'+name,required=True)
    parser.add_argument('--project')
    args = parser.parse_args()
    try:
        inputs = [json.loads(Path(getattr(args,n)).read_text(encoding='utf-8')) for n in ('plan','run','config','host')]
        ctx = live_context(args.plan, args.project) if inputs[0].get('schema_version') == 2 else None
        result = propose(*inputs, context=ctx)
        print(json.dumps(result,indent=2)); sys.exit(bool(result['errors']))
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        raise SystemExit('Routing refused: ' + str(exc))
