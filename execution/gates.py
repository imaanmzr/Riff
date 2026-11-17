"""Record validation only: claims must be independently checked against evidence."""
import json
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'planning'))
from validate import validate as validate_plan
from riff_core.records import digest, load
from riff_core.config import context as live_context

STATES = {'pending', 'running', 'review', 'blocked', 'integrated'}


def simulated(value):
    if isinstance(value, dict):
        return value.get('simulated') is True or value.get('simulation') is True or any(simulated(v) for v in value.values())
    return isinstance(value, list) and any(simulated(v) for v in value)


def execution_context(plan, run, context):
    """Advance source freshness only with current reviewed integration evidence."""
    result = dict(context or {})
    if plan.get('schema_version') != 2 or not run.get('source_manifest'):
        return result
    review = run.get('source_manifest_review', {})
    if not isinstance(run['source_manifest'], dict):
        raise ValueError('Execution source manifest must be an object')
    if set(plan.get('source_manifest', {})) - set(run['source_manifest']):
        raise ValueError('Execution source manifest omits reviewed paths; represent verified removals with null')
    valid = (review.get('verdict') == 'pass' and review.get('revision') == run.get('head_revision')
             and review.get('manifest_digest') == digest(run['source_manifest'])
             and review.get('reviewer') and review.get('evidence') and not simulated(review)
             and (plan.get('route') == 'small' or
                  (review.get('independent') is True and review.get('reviewer') != run.get('integration_owner')))
             and any(r.get('state') == 'integrated' and r.get('integration_revision') == run.get('head_revision')
                     and passed(r, r.get('candidate_revision'), r.get('agent'), plan.get('route') != 'small',
                                ['spec', 'quality'] + (['invariants'] if plan.get('route') == 'critical' else []))
                     for r in run.get('tasks', {}).values()))
    if not valid: raise ValueError('Execution source manifest lacks current independent integration evidence')
    result['source_manifest'] = run['source_manifest']
    return result


def passed(bundle, revision, author, independent, kinds):
    checks = bundle.get('checks', [])
    reviews = bundle.get('reviews', [])
    return (not simulated(bundle) and bool(revision) and bool(checks) and
        all(c.get('revision') == revision and c.get('exit_code') == 0 and
            c.get('command') and c.get('evidence') for c in checks) and
        all(any(r.get('kind') == kind and r.get('revision') == revision and
            r.get('verdict') == 'pass' and r.get('reviewer') and r.get('evidence') and
            (not independent or (r.get('independent') is True and r['reviewer'] != author))
            for r in reviews) for kind in kinds) and not bundle.get('blockers'))


def validate(plan, run, context=None):
    if not isinstance(run, dict): return ['Execution record must be an object']
    try:
        context = execution_context(plan, run, context)
    except (ValueError, TypeError, AttributeError) as exc:
        return [str(exc)]
    errors = validate_plan(plan, context)
    if simulated(run) or simulated(plan): errors.append('Simulated evidence cannot qualify for execution')
    if errors: return errors
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


def ready(plan, run, context=None):
    if validate(plan, run, context) or run.get('status') != 'running': return []
    records = run['tasks']
    return [t['id'] for t in plan['tasks'] if records[t['id']]['state'] == 'pending'
            and all(records[d]['state'] == 'integrated' for d in t.get('dependencies', []))]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan')
    parser.add_argument('run')
    parser.add_argument('--project')
    args = parser.parse_args()
    try:
        plan, run = load(args.plan), load(args.run)
        ctx = live_context(args.plan, args.project) if plan.get('schema_version') == 2 else None
        errors = validate(plan, run, ctx)
        print(json.dumps({'errors': errors, 'eligible_tasks': ready(plan, run, ctx)}, indent=2))
        sys.exit(bool(errors))
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print('Invalid input: ' + str(exc)); sys.exit(1)
