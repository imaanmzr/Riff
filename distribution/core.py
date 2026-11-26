"""Use exactly the reference implementation shipped with this installation."""
from pathlib import Path
import sys

REFERENCES = Path(__file__).resolve().parent / 'skills' / 'riff' / 'references'
for phase in ('planning', 'execution', 'recovery', 'routing'):
    sys.path.insert(0, str(REFERENCES / phase))

from riff_core import records, config, diagnostics, storage, progress, onboarding
import gates
import state as recovery


def inspect(directory, project):
    plan = records.load(directory / 'plan.json')
    run = records.load(directory / 'run.json') if (directory / 'run.json').exists() else None
    ctx = {'task_dir': directory, 'project': project, 'effective_behavior': config.resolve(project, plan)['behavior']}
    errors, eligible = [], []
    if run is not None:
        errors = gates.validate(plan, run, ctx)
        eligible = gates.ready(plan, run, ctx)
        try:
            ctx = gates.execution_context(plan, run, ctx)
        except ValueError:
            pass  # The execution error above remains visible and blocking.
    report = diagnostics.evaluate(plan, ctx, run, errors, eligible)
    current = progress.summarize(directory, plan, run or {}, report, project=project)
    report.update(next_action=current['next_action'], next_command=current['next_command'], progress=current)
    return plan, run, report
