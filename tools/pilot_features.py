"""Repeatable local feature pilots; fixtures are not independent human reviews."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'planning'))
from riff_core import reports
from riff_core.diagnostic_runner import run


def main():
    output = ROOT / 'build/pilots'
    output.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(prefix='riff-pilots-') as temporary:
        project = Path(temporary)
        (project / '.riff').mkdir()
        (project / '.riff/project.json').write_text('{}')
        commands = []
        def cli(*args):
            started = time.monotonic()
            result = subprocess.run([sys.executable, str(ROOT / 'riff.py'), *args, '--project', str(project)],
                                    capture_output=True, text=True, encoding='utf-8', timeout=30)
            commands.append({'argv': list(args), 'exit_code': result.returncode, 'seconds': time.monotonic()-started})
            if result.returncode: raise RuntimeError(result.stderr or result.stdout)
            return result
        start = time.monotonic()
        cli('new', 'small', '--route', 'small', '--profile', 'documentation', '--detail', 'concise')
        task = project / 'docs/work/small'
        (task / 'plan.md').write_text('# Improve setup wording\n\nClarify that workflow commands print prompts.\n')
        plan = json.loads((task / 'plan.json').read_text())
        plan['outcome'] = 'The setup guide tells readers where to paste the generated prompt.'
        (task / 'plan.json').write_text(json.dumps(plan))
        cli('show', 'small')
        cli('render', 'small', '--output', str(output / 'small.md'), '--overwrite')
        results.append({'scenario': 'small documentation plan', 'kind': 'controlled local fixture',
                        'accepted_requirements': ['concise summary', 'explicit omitted-detail notice'],
                        'seconds': time.monotonic()-start, 'status': 'passed'})
        start = time.monotonic()
        cli('new', 'feature', '--title', 'Explain task readiness')
        task = project / 'docs/work/feature'
        plan = json.loads((task / 'plan.json').read_text())
        plan['outcome'] = 'Users can see why a task is blocked and what to do next.'
        plan['tasks'] = [dict(id='T1', objective='Collect diagnostic evidence', dependencies=[], requirements=[]),
                         dict(id='T2', objective='Present the next action', dependencies=['T1'], requirements=[])]
        (task / 'plan.json').write_text(json.dumps(plan))
        (task / 'plan.md').write_text('''# Explain readiness

## Current problem
A saved status does not explain whether its evidence is still current.

## Proposed interaction
Illustrative sequence for this pilot; not an implemented server protocol.

```mermaid
sequenceDiagram
    User->>Riff: Explain this task
    Riff->>Records: Read current evidence
    Records-->>Riff: Review is stale
    Riff-->>User: Re-review changed source
```

## Acceptance
Show the saved status separately from the current evaluation. Missing evidence
must remain unknown. Do not treat a diagram as proof of implementation.
''', encoding='utf-8')
        cli('render', 'feature', '--format', 'html', '--output', str(output / 'feature.html'), '--overwrite')
        cli('graph', 'feature')
        results.append({'scenario': 'feature plan with dependencies and sequence', 'kind': 'controlled local fixture',
                        'accepted_requirements': ['full narrative', 'dependency graph', 'self-contained HTML'],
                        'seconds': time.monotonic()-start, 'status': 'passed'})
        start = time.monotonic()
        report = json.loads((ROOT / 'planning/templates/research.json').read_text())
        report.update(status='inconclusive', question='Which host is cheapest for this workflow?', scope='Repository evidence only',
                      success_criteria='A defensible cost comparison', limits='No live provider calls or fabricated usage',
                      sources=[{'id':'S1','source':'README.md','revision':hashlib.sha256((ROOT/'README.md').read_bytes()).hexdigest()}],
                      claims=[{'id':'Q1','text':'No measured host comparison is available in this pilot.','classification':'unresolved','sources':['S1']}],
                      uncertainty=['Actual model usage and quality on equivalent tasks are unmeasured'],
                      conclusion='No cheapest host can be established.',next_action='Run authorized equivalent-task benchmarks before making a cost claim.')
        assert reports.validate(report) == []
        (output / 'research.json').write_text(json.dumps(report, indent=2))
        cli('research', 'Compare hosts without inventing costs')
        results.append({'scenario':'inconclusive research', 'kind':'repository-limited investigation',
                        'accepted_requirements':['explicit uncertainty', 'no fabricated ranking'],
                        'seconds':time.monotonic()-start,'status':'passed'})
        start = time.monotonic()
        isolated = project / 'reproduction'
        isolated.mkdir()
        fixture = isolated / 'bug.py'
        fixture.write_text('def decrement(n):\n    return n + 1\nassert decrement(2) == 1, "decrement returned the wrong value"\n')
        original = fixture.read_bytes()
        observation = run([sys.executable, str(fixture)], isolated, command_timeout=5, total_timeout=10)
        assert observation['exit_code'] != 0 and not observation['timed_out'] and fixture.read_bytes() == original
        report = json.loads((ROOT / 'planning/templates/debug.json').read_text())
        report.update(status='complete',expected='decrement(2) returns 1',actual='decrement(2) returns 3',
                      environment={'python':sys.version.split()[0], 'fixture':'controlled arithmetic defect'},
                      evidence=[{'id':'E1','source':'isolated bug.py and captured assertion','revision':hashlib.sha256(original).hexdigest()}],
                      reproductions=[dict(observation,id='P1',evidence=['E1'])],
                      hypotheses=[{'id':'H1','text':'Addition is used instead of subtraction','status':'supported','evidence':['E1']}],
                      causal_evidence=['E1'], proposed_fix='Subtract one after a separate implementation request.',
                      regression_checks=['decrement(2) == 1'],next_action='Plan and review the fix; no product edit was made.')
        assert reports.validate(report) == []
        (output / 'debug.json').write_text(json.dumps(report, indent=2))
        results.append({'scenario':'reproduced bug', 'kind':'controlled isolated defect, not a production claim',
                        'accepted_requirements':['actual failing reproduction', 'process cleanup', 'no product edits'],
                        'seconds':time.monotonic()-start,'status':'passed'})
    evidence = {'scenarios':results, 'commands':commands, 'defects_after_completion':None,
                'rework':'See execution-log.md for defects found and fixed during review.',
                'readability_feedback':'Independent agent review of the small pilot found an unclear outcome fallback and excessive diagnostics. The pilot now has a structured outcome and concise views show the first three findings. Human feedback was not collected.',
                'model_usage':'Unavailable; no usage or cost improvement claimed.',
                'live_host_pilots':'Not performed; live adapters are outside this release.',
                'outputs':'build/pilots (regenerate with tools/pilot_features.py)'}
    target = ROOT / 'docs/work/riff-expansion/pilots.json'
    target.write_text(json.dumps(evidence, indent=2)+'\n',encoding='utf-8')
    print('Passed four local pilots; reports: ' + str(target))


if __name__ == '__main__': main()
