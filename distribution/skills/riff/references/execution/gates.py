"""Record validation only: claims must be independently checked against evidence."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'planning'))
from validate import validate as validate_plan

STATES = {'pending', 'running', 'review', 'blocked', 'integrated'}


def passed(bundle, revision, author, independent, kinds):
    checks = bundle.get('checks', [])
    reviews = bundle.get('reviews', [])
    return (bool(revision) and bool(checks) and
        all(c.get('revision') == revision and c.get('exit_code') == 0 and
            c.get('command') and c.get('evidence') for c in checks) and
        all(any(r.get('kind') == kind and r.get('revision') == revision and
            r.get('verdict') == 'pass' and r.get('reviewer') and r.get('evidence') and
            (not independent or (r.get('independent') is True and r['reviewer'] != author))
            for r in reviews) for kind in kinds) and not bundle.get('blockers'))


def validate(plan, run):
    errors = validate_plan(plan)
    if plan.get('status') != 'READY': errors.append('Plan is not READY')
    if run.get('plan_revision') != plan.get('revision') or run.get('base_revision') != plan.get('source_revision'):
        errors.append('Execution does not match reviewed plan baseline')
    if run.get('authorized') is not True: errors.append('Execution authorization missing')
    tasks = {t['id']: t for t in plan.get('tasks', [])}
    records = run.get('tasks', {})
    if set(records) != set(tasks): errors.append('Execution task set differs from plan')
    independent = plan.get('route') != 'small'
    for tid, r in records.items():
        state = r.get('state')
        if state not in STATES: errors.append(tid + ': invalid state')
        if state == 'blocked' and not r.get('reason'): errors.append(tid + ': missing block reason')
        if state in ('running', 'review', 'integrated'):
            if not r.get('agent'): errors.append(tid + ': missing agent')
            if any(records.get(d, {}).get('state') != 'integrated' for d in tasks.get(tid, {}).get('dependencies', [])):
                errors.append(tid + ': dependency not integrated')
        if state == 'integrated':
            kinds = ['spec', 'quality'] + (['invariants'] if plan.get('route') == 'critical' else [])
            if not r.get('integration_revision') or not passed(r, r.get('candidate_revision'), r.get('agent'), independent, kinds):
                errors.append(tid + ': missing current checks or reviews')
    if run.get('status') not in ('running', 'blocked', 'complete'): errors.append('Invalid execution status')
    if run.get('status') == 'complete':
        if not records or any(r.get('state') != 'integrated' for r in records.values()): errors.append('Unfinished tasks')
        final = run.get('final', {})
        if not passed(final, run.get('head_revision'), run.get('integration_owner'), independent, ['integration']):
            errors.append('Missing final integrated verification/review')
        if set(plan.get('requirements', [])) - set(final.get('requirements', [])):
            errors.append('Final requirement coverage incomplete')
    if run.get('blockers'): errors.append('Execution has unresolved blockers')
    return errors


def ready(plan, run):
    if validate(plan, run) or run.get('status') != 'running': return []
    records = run['tasks']
    return [t['id'] for t in plan['tasks'] if records[t['id']]['state'] == 'pending'
            and all(records[d]['state'] == 'integrated' for d in t.get('dependencies', []))]


if __name__ == '__main__':
    try:
        plan, run = [json.loads(Path(p).read_text()) for p in sys.argv[1:]]
        errors = validate(plan, run)
        print(json.dumps({'errors': errors, 'eligible_tasks': ready(plan, run)}, indent=2))
        sys.exit(bool(errors))
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print('Invalid input: ' + str(exc)); sys.exit(1)
