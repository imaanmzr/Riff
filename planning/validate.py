"""Shared structural and live-binding checks; not proof of semantic correctness."""
import argparse
import sys
from riff_core.records import validate, load
from riff_core.config import context

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan')
    parser.add_argument('--project')
    args = parser.parse_args()
    try:
        plan = load(args.plan)
        ctx = context(args.plan, args.project) if plan.get('schema_version') == 2 else None
        errors = validate(plan, ctx)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors = ['Invalid input: ' + str(exc)]
    print('\n'.join(errors) if errors else 'Structural checks passed; semantic review still required.')
    sys.exit(bool(errors))
