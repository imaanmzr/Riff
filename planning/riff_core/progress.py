"""Derived progress shared by CLI status and generated handoffs; never grants readiness."""
from collections import Counter
import os
import re
import shlex

from . import records


def _objects(value):
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _messages(value):
    if not isinstance(value, list):
        return []
    return list(dict.fromkeys(str(item) for item in value if item))


def _partition(items, current):
    result = dict(current=[], historical=[], unbound=[])
    for item in _objects(items):
        bucket = 'unbound' if item.get('revision') is None else 'current' if current(item) else 'historical'
        result[bucket].append(item)
    return result


def _plan_reviews(plan):
    def current(review):
        if review.get('revision') != plan.get('revision') or review.get('source_revision') != plan.get('source_revision'):
            return False
        if plan.get('schema_version', 1) == 2:
            expected = dict(authored_digest=plan.get('authored_digest'), config_digest=plan.get('config_digest'),
                            plan_digest=records.plan_digest(plan))
            return all(value and review.get(key) == value for key, value in expected.items())
        return True
    result = _partition(plan.get('reviews'), current)
    result['verdicts'] = dict(Counter(r.get('verdict', 'unknown') for r in result['current']))
    return result


def _task(plan, task, record, eligible):
    if not isinstance(record, dict):
        raise ValueError('Each execution task must be an object')
    candidate = record.get('candidate_revision')
    current = lambda item: bool(candidate) and item.get('revision') == candidate
    checks = _partition(record.get('checks'), current)
    checks.update(passed=sum(type(c.get('exit_code')) is int and c['exit_code'] == 0
                             and bool(c.get('command')) and bool(c.get('evidence'))
                             and not records.simulated(c) for c in checks['current']),
                  failed=sum(type(c.get('exit_code')) is int and c['exit_code'] != 0 for c in checks['current']),
                  unknown=0)
    checks['unknown'] = len(checks['current']) - checks['passed'] - checks['failed']
    reviews = _partition(record.get('reviews'), current)
    required = ['spec', 'quality'] + (['invariants'] if plan.get('route') == 'critical' else [])
    independent = plan.get('route') != 'small'
    def passes(review):
        return (review.get('verdict') == 'pass' and review.get('reviewer') and review.get('evidence')
                and not records.simulated(review)
                and (not independent or (review.get('independent') is True and review['reviewer'] != record.get('agent'))))
    reviews['passed_kinds'] = [kind for kind in required if any(r.get('kind') == kind and passes(r) for r in reviews['current'])]
    reviews['missing_kinds'] = [kind for kind in required if kind not in reviews['passed_kinds']]
    reviews['verdicts_by_kind'] = {kind: [r.get('verdict', 'unknown') for r in reviews['current'] if r.get('kind') == kind]
                                   for kind in required}
    rejected = [r.get('kind', 'unspecified') for r in reviews['current'] if r.get('verdict') in ('fail', 'changes-required', 'reject')]
    state = record.get('state', 'not started')
    blockers = _messages(record.get('blockers'))
    if record.get('reason'):
        blockers.insert(0, str(record['reason']))
    result = dict(id=task.get('id'), objective=task.get('objective', ''), state=state,
                  candidate_revision=candidate, integration_revision=record.get('integration_revision'),
                  dependencies=task.get('dependencies', []), checks=checks, reviews=reviews,
                  blockers=list(dict.fromkeys(blockers)), agent=record.get('agent'),
                  eligible=task.get('id') in eligible)
    result['_rejected'] = rejected
    return result


def _next(directory, plan, run, evaluation, items):
    task_id = directory.name
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', task_id):
        return 'repair', 'Rename the invalid task directory before generating a continuation command.', []
    command = lambda *args: ['riff', *args]
    if evaluation.get('checks', {}).get('structure') == 'fail':
        return 'repair', 'Repair the invalid record structure, then check this task again.', command('check', task_id)
    if plan.get('schema_version', 1) == 1:
        return 'migration', 'Preview the legacy-to-v2 upgrade; complete its bindings and review/reconcile before resuming implementation.', command('migrate', task_id)
    if plan.get('unresolved_questions'):
        return 'clarification', 'Resolve the recorded material questions with their owners, then continue planning.', command('plan', '--task', task_id)
    if plan.get('blockers'):
        return 'planning', 'Resolve the recorded plan blockers and renew affected review before execution.', command('plan', '--task', task_id)
    if plan.get('status') != 'READY':
        return 'planning', 'Complete or revise the plan and obtain a current qualifying review before implementation.', command('plan', '--task', task_id)
    checks = evaluation.get('checks', {})
    if checks.get('freshness') in ('fail', 'unknown'):
        return 'reconciliation', 'Reconcile changed source/authored/configuration bindings and renew affected reviews.', command('resume', task_id)
    if checks.get('review') != 'pass':
        return 'plan review', 'Obtain a current qualifying plan review before dispatch.', command('review', '--task', task_id)
    if run and (run.get('plan_revision') != plan.get('revision') or run.get('base_revision') != plan.get('source_revision')):
        return 'reconciliation', 'Reconcile the execution record with the currently reviewed plan revision and baseline.', command('resume', task_id)
    issues = evaluation.get('issues', [])
    authorization_only = bool(issues) and all(i.get('category') == 'execution'
                                             and i.get('message') == 'Execution authorization missing' for i in issues)
    if (evaluation.get('evaluated_status') != 'READY' and not authorization_only) or run.get('status') == 'blocked':
        return 'reconciliation', evaluation.get('next_action', 'Resolve execution/recovery blockers before dispatch.'), command('resume', task_id)
    if not run or run.get('authorized') is not True:
        return 'authorization', 'Execution needs explicit authorization for this reviewed plan. Generate an execution request for the agent.', command('execute', task_id)
    active = [t for t in items if t['state'] in ('running', 'review', 'blocked')]
    rejected = next((t for t in active if any(r.get('verdict') in ('fail', 'changes-required', 'reject')
                                            for r in t['reviews']['current'])), None)
    focus = rejected or next(iter(active), None)
    if focus:
        phase = 'review' if focus['state'] == 'review' else 'implementation'
        return phase, focus['id'] + ': ' + focus['next_action'], command('resume', task_id)
    if run.get('status') == 'complete':
        return 'complete', 'Execution and final integration evidence are current. No implementation task remains.', []
    if items and all(t['state'] == 'integrated' for t in items):
        return 'integration', 'Run final integrated verification and obtain the final integration review before marking execution complete.', command('resume', task_id)
    eligible = [t['id'] for t in items if t['eligible']]
    if eligible:
        return 'implementation', 'Next eligible task(s): ' + ', '.join(eligible) + '. Respect existing authorization, scope and capacity.', command('resume', task_id)
    return 'waiting', 'No task is currently eligible; inspect dependency and execution blockers.', command('explain', task_id)


def _command(argv):
    if not argv:
        return None
    if os.name == 'nt':
        return ' '.join(arg if re.fullmatch(r'[A-Za-z0-9_./:-]+', arg) else "'" + arg.replace("'", "''") + "'" for arg in argv)
    return shlex.join(argv)


def summarize(directory, plan, run, evaluation, project=None):
    records = run.get('tasks', {})
    if not isinstance(records, dict):
        raise ValueError('Execution tasks must be an object')
    eligible = evaluation.get('eligible_tasks', []) if evaluation.get('evaluated_status') == 'READY' else []
    items = [_task(plan, t, records.get(t.get('id'), {}), eligible)
             for t in _objects(plan.get('tasks'))]
    states = {t['id']: t['state'] for t in items}
    for item in items:
        item['waiting_for'] = [d for d in item['dependencies'] if states.get(d) != 'integrated']
        state = item['state']
        if item['_rejected']:
            action = 'Address current ' + ', '.join(item['_rejected']) + ' review findings, verify, then request re-review.'
        elif item['blockers']:
            action = 'Resolve: ' + '; '.join(item['blockers'])
        elif item['checks']['failed']:
            action = 'Fix the failed current-candidate checks and repeat affected verification.'
        elif item['waiting_for']:
            action = 'Wait for integration of ' + ', '.join(item['waiting_for']) + '.'
        elif item['checks']['unknown']:
            action = 'Complete the current check command, exit code and evidence records before integration.'
        elif state in ('running', 'review') and item['checks']['passed'] and item['reviews']['missing_kinds']:
            action = 'Request current ' + ', '.join(item['reviews']['missing_kinds']) + ' reviews before integration.'
            if any(r.get('verdict') in ('changes-required', 'fail') for r in item['reviews']['historical']):
                action = 'Verify fixes from historical changes-required findings; ' + action[0].lower() + action[1:]
        elif state == 'integrated':
            action = 'Preserve the integrated evidence; revalidate it if affected inputs change.'
        elif state == 'review' and item['checks']['passed'] and not item['reviews']['missing_kinds']:
            action = 'Current check/review records are complete; integrate the reviewed candidate under the project workflow.'
        elif state in ('running', 'review'):
            action = 'Continue verification and current-candidate review; no integration is implied.'
        elif item['eligible']:
            action = 'Eligible under current gates; dispatch only within existing authorization and capacity.'
        else:
            action = 'Pending; resolve plan/recovery gates before dispatch.'
        item['next_action'] = action
        del item['_rejected']
    counts = Counter(t['state'] for t in items)
    progress = {key: counts.get(key, 0) for key in ('integrated', 'running', 'review', 'blocked', 'pending', 'not started')}
    progress['total'] = len(items)
    if counts.get('unknown'):
        progress['unknown'] = counts['unknown']
    active = [t for t in items if t['state'] in ('running', 'review')]
    frontier = [t for t in items if t['state'] != 'integrated' and not t['waiting_for']]
    focus = next(iter(active or frontier), None)
    phase, next_action, argv = _next(directory, plan, run, evaluation, items)
    work_allowed = (evaluation.get('evaluated_status') == 'READY' and plan.get('status') == 'READY'
                    and plan.get('schema_version') == 2
                    and run.get('authorized') is True and run.get('status') == 'running'
                    and run.get('plan_revision') == plan.get('revision')
                    and run.get('base_revision') == plan.get('source_revision'))
    if not work_allowed:
        for item in items:
            item['eligible'] = False
            if item['state'] != 'integrated':
                item['next_action'] = 'Resolve current plan/readiness/authorization gates before continuing this task.'
    availability = plan.get('capability_availability', {})
    host = availability.get('host') if isinstance(availability, dict) else None
    if argv and argv[1] in ('plan', 'review', 'resume', 'execute') and host in ('codex', 'cursor', 'claude', 'vscode'):
        argv += ['--host', host]
    if argv and project is not None:
        argv += ['--project', str(project)]
    current_evaluation = dict(evaluation, next_action=next_action, next_command=_command(argv))
    return dict(task=directory.name, title=plan.get('title') or plan.get('id') or directory.name,
                plan_status=plan.get('status', 'unknown'), plan_revision=plan.get('revision'),
                schema_version=plan.get('schema_version', 1), phase=phase,
                source_revision=plan.get('source_revision'), route=plan.get('route'),
                execution_status=run.get('status', 'not started'), authorized=run.get('authorized') is True,
                blockers=_messages(run.get('blockers')) + _messages(plan.get('blockers')),
                parent=plan.get('parent'), recorded_next_action=plan.get('next_action'),
                external_prerequisites=_objects(plan.get('external_prerequisites', run.get('external_prerequisites'))),
                progress=progress, reviews=dict(plan=_plan_reviews(plan)), tasks=items, evaluation=current_evaluation,
                next_action=next_action, next_command=_command(argv), next_command_argv=argv,
                current_work=dict(task=focus['id'], next_action=focus['next_action']) if focus else None,
                records_directory=str(directory))


def _line(value, limit=220):
    text = ' '.join(str(value).split())
    text = ''.join(c for c in text if c.isprintable())
    return text if len(text) <= limit else text[:limit - 3] + '...'


def render(item, details=False, all_tasks=False):
    p = item['progress']; review = item['reviews']['plan']; evaluation = item['evaluation']
    lines = [f"{item['task']}: { _line(item['title']) }",
             f"  Plan: {item['plan_status']} r{item['plan_revision']} ({item['route']}, schema {item['schema_version']}); execution={item['execution_status']}; authorized={item['authorized']}",
             f"  Evaluated: {evaluation['evaluated_status']}; " + ', '.join(f'{k}={v}' for k, v in evaluation['checks'].items()),
             f"  Progress: {p['integrated']}/{p['total']} integrated (recorded); " + ', '.join(f'{n} {s}' for s, n in p.items() if s not in ('total', 'integrated') and n),
             f"  Plan reviews: {len(review['current'])} current {review['verdicts']}; {len(review['historical'])} historical; {len(review['unbound'])} unbound"]
    if item['parent']:
        lines.append('  Parent: ' + _line(item['parent']))
    interesting = [t for t in item['tasks'] if t['state'] in ('running', 'review', 'blocked')]
    for t in item['tasks']:
        if t not in interesting and t['state'] != 'integrated':
            interesting.append(t)
            break
    shown = item['tasks'] if details or all_tasks else interesting[:5]
    for t in shown:
        r = t['reviews']; c = t['checks']
        waiting = '; waits ' + ', '.join(t['waiting_for']) if t['waiting_for'] else ''
        lines.append(f"  {t['id']} [{t['state']}]{waiting}: " + _line(t['objective']))
        lines.append(f"    Checks: {c['passed']} pass / {c['failed']} fail / {c['unknown']} unknown current; {len(c['historical'])} historical, {len(c['unbound'])} unbound. Reviews: {len(r['current'])} current, {len(r['historical'])} historical; missing " + (', '.join(r['missing_kinds']) or 'none'))
        if r['current']:
            lines.append('    Current review verdicts: ' + '; '.join(kind + '=' + ','.join(verdicts) for kind, verdicts in r['verdicts_by_kind'].items() if verdicts))
        old_rejections = [x for x in r['historical'] if x.get('verdict') in ('changes-required', 'fail')]
        if old_rejections:
            lines.append('    Historical changes-required: ' + ', '.join(str(x.get('kind', 'unspecified')) for x in old_rejections) + ' (does not review the current candidate).')
        lines.append('    Next: ' + _line(t['next_action']))
        if details:
            lines.append('    Candidate: ' + str(t['candidate_revision'] or 'unbound'))
            for bucket in ('current', 'historical', 'unbound'):
                for x in r[bucket]:
                    lines.append(f"    Review [{bucket}] {x.get('kind', 'unspecified')}: {x.get('verdict', 'unknown')} by {_line(x.get('reviewer', 'unknown'))}; " + _line(x.get('evidence', x.get('notes', 'No evidence recorded'))))
    if len(shown) < len(interesting):
        lines.append(f'  {len(interesting) - len(shown)} more active/waiting tasks; use --details for all tasks.')
    issues = evaluation.get('issues', [])
    for issue in issues if details else issues[:3]:
        lines.append(f"  [{issue['category']}: {issue['state']}] " + _line(issue['message']))
    if not details and len(issues) > 3:
        lines.append(f'  {len(issues) - 3} more gate issues; use --details or riff explain.')
    for prerequisite in item['external_prerequisites']:
        lines.append('  Prerequisite ' + _line(prerequisite.get('id', 'unknown')) + ': ' + _line(prerequisite.get('requirement', prerequisite.get('status', 'unknown'))))
    lines.append('  Next: ' + _line(item['next_action']))
    if item['next_command']:
        lines.append('  Command: ' + item['next_command'])
    if item['current_work']:
        lines.append('  Current work: ' + item['current_work']['task'] + ' - ' + _line(item['current_work']['next_action']))
    if item['recorded_next_action']:
        lines.append('  Recorded handoff: ' + _line(item['recorded_next_action']))
    lines.append('  Records: ' + item['records_directory'])
    return '\n'.join(lines)
