"""Explain saved state separately from current evaluated readiness."""
import copy
from . import records


def evaluate(plan, context, run=None, execution_errors=None, eligible=None):
    issues = []
    def add(category, state, message, remedy):
        item = dict(category=category, state=state, message=message, remedy=remedy)
        if item not in issues: issues.append(item)

    draft = copy.deepcopy(plan)
    draft['status'] = 'DRAFT'
    structure = records.validate(draft)
    for error in structure:
        add('structure', 'fail', error, 'Repair the referenced record; run riff check again.')
    if structure:
        return dict(recorded_status=str(plan.get('status', 'unknown')), evaluated_status='BLOCKED',
                    checks={'structure': 'fail', 'review': 'unknown', 'freshness': 'unknown', 'execution': 'unknown', 'readiness': 'fail'},
                    issues=issues, eligible_tasks=[], next_action='Repair invalid record structure before evaluating evidence.')
    for question in plan.get('unresolved_questions', []):
        add('question', 'fail', str(question), 'Resolve the question and record its evidence.')
    for blocker in plan.get('blockers', []):
        add('blocker', 'fail', str(blocker), 'Record resolution evidence before clearing the blocker.')
    if plan.get('status') != 'READY':
        add('review', 'fail', 'Recorded plan is ' + str(plan.get('status', 'unknown')),
            'Complete planning and obtain a current qualifying review.')
    candidate = copy.deepcopy(plan)
    candidate['status'] = 'READY'
    for error in records.validate(candidate, context):
        if error == 'Unresolved blockers or questions' and (plan.get('unresolved_questions') or plan.get('blockers')):
            continue  # Individual blockers above have more context.
        category = ('freshness' if any(word in error.lower() for word in ('source changed', 'freshness', 'authored', 'configuration', 'live review'))
                    else 'review' if 'review' in error.lower() or 'simulated' in error.lower() else 'readiness')
        state = 'unknown' if 'unavailable' in error.lower() or 'unknown:' in error.lower() else 'fail'
        add(category, state, error, 'Update the referenced evidence and re-review the affected plan.')
    if plan.get('schema_version', 1) == 1:
        add('freshness', 'unknown', 'Legacy records do not bind live authored content and configuration.',
            'Preview riff migrate; complete v2 evidence before claiming verified freshness.')
    for error in execution_errors or []:
        add('execution', 'fail', error, 'Inspect execution evidence and reconcile state before dispatch.')
    for blocker in (run or {}).get('blockers', []):
        add('execution', 'fail', str(blocker), 'Resolve through recovery with evidence.')
    for identity, task in (run or {}).get('tasks', {}).items():
        if task.get('state') == 'blocked':
            add('execution', 'fail', f"{identity}: {task.get('reason') or 'Task is blocked'}",
                'Inspect the task and record resolution evidence before returning it to pending.')
    categories = ('structure', 'review', 'freshness', 'execution')
    checks = {}
    for category in categories:
        states = [i['state'] for i in issues if i['category'] == category]
        checks[category] = ('fail' if 'fail' in states else 'unknown' if 'unknown' in states else
                            'not applicable' if category == 'execution' and run is None else 'pass')
    # Readiness errors include live-binding failures even when other categories pass.
    checks['readiness'] = 'fail' if any(i['state'] == 'fail' for i in issues) else 'unknown' if issues else 'pass'
    if issues:
        next_action = next((item['remedy'] for item in issues if item['state'] == 'fail'), issues[0]['remedy'])
    elif run is None:
        next_action = 'Plan evidence is current. Execution requires authorization.'
    elif eligible:
        next_action = 'Eligible for routing: ' + ', '.join(eligible) + '.'
    elif run.get('status') == 'complete':
        next_action = 'Execution record is complete. Inspect the integrated verification and review.'
    else:
        next_action = 'No task is eligible. Inspect active work and pending dependencies.'
    return dict(recorded_status=plan.get('status', 'unknown'),
                evaluated_status='READY' if not issues else 'BLOCKED', checks=checks, issues=issues,
                eligible_tasks=eligible or [],
                next_action=next_action)


def text_report(plan, report):
    lines = [plan.get('title', plan.get('task_id', 'Riff task')),
             'Recorded status: ' + report['recorded_status'],
             'Evaluated status: ' + report['evaluated_status']]
    for item in report['issues']:
        lines += [f"- [{item['state']}] {item['message']}", '  Next: ' + item['remedy']]
    lines.append('Next action: ' + report['next_action'])
    return '\n'.join(lines)
