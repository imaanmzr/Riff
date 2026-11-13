"""Structural checks only; review and evidence require human/agent inspection."""
import json
import sys


def validate(p):
    errors = []
    tasks = p.get('tasks', [])
    ids = [t['id'] for t in tasks]
    if len(ids) != len(set(ids)):
        errors.append('Duplicate task IDs')
    graph = {t['id']: t.get('dependencies', []) for t in tasks}
    visiting, visited = set(), set()

    def visit(node):
        if node not in graph:
            errors.append('Unknown dependency: ' + node)
            return
        if node in visiting:
            errors.append('Dependency cycle: ' + node)
            return
        if node in visited:
            return
        visiting.add(node)
        for dep in graph[node]:
            visit(dep)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)
    if p.get('status') == 'READY':
        if not tasks or not p.get('requirements'):
            errors.append('Ready plan needs requirements and tasks')
        covered = set()
        for task in tasks:
            covered.update(task.get('requirements', []))
            for field in ('objective', 'inputs', 'scope', 'outputs', 'owner',
                          'capability', 'reviewer', 'verification'):
                if not task.get(field):
                    errors.append(task['id'] + ': missing ' + field)
        if set(p.get('requirements', [])) - covered:
            errors.append('Uncovered requirements')
        if p.get('blockers') or p.get('unresolved_questions'):
            errors.append('Unresolved blockers or questions')
        if not p.get('revision') or not p.get('source_revision'):
            errors.append('Missing revision binding')
        reviews = p.get('reviews', [])
        if not any(r.get('revision') == p.get('revision') and
                   r.get('source_revision') == p.get('source_revision') and
                   r.get('verdict') == 'pass' and r.get('reviewer') and
                   (p.get('route') == 'small' or r.get('independent') is True)
                   for r in reviews):
            errors.append('Missing current qualifying review')
    if p.get('route') not in ('small', 'standard', 'complex', 'critical'):
        errors.append('Invalid route')
    if p.get('status') not in ('DRAFT', 'BLOCKED', 'CONDITIONAL', 'READY'):
        errors.append('Invalid status')
    return errors


if __name__ == '__main__':
    try:
        errors = validate(json.load(open(sys.argv[1])))
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        errors = ['Invalid input: ' + str(exc)]
    print('\n'.join(errors) if errors else 'Structural checks passed; semantic review still required.')
    sys.exit(bool(errors))
