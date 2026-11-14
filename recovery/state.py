"""Local atomic checkpoints and conservative recovery; never replays side effects."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile

if os.name == 'nt':
    import msvcrt
else:
    import fcntl


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def fingerprint(root, paths):
    root = Path(root).resolve()
    result = {}
    for name in paths:
        p = root / name
        if Path(name).is_absolute() or '..' in Path(name).parts or p.is_symlink():
            raise ValueError('Unsafe manifest path: ' + name)
        if not p.resolve().is_relative_to(root):
            raise ValueError('Path escapes root: ' + name)
        if p.is_file():
            result[name] = hashlib.sha256(p.read_bytes()).hexdigest()
        elif not p.exists():
            result[name] = None
        else:
            raise ValueError('Manifest entries must be files: ' + name)
    return result


def load(path):
    value = json.loads(Path(path).read_text())
    if value.get('schema') != 1 or value.get('checksum') != digest(value.get('payload')):
        raise ValueError('Invalid or corrupt checkpoint')
    return value['payload']


def save(path, payload, expected_generation):
    """CAS under a local advisory lock; no silent last-writer-wins updates."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(path) + '.lock', 'a+b') as lock:
        if os.name == 'nt':
            # Windows can lock a byte beyond EOF, so existing empty lock files work.
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            fcntl.flock(lock, fcntl.LOCK_EX)
        current = load(path)['generation'] if path.exists() else 0
        if current != expected_generation:
            raise ValueError('Stale checkpoint generation')
        data = copy.deepcopy(payload)
        data['generation'] = current + 1
        envelope = dict(schema=1, payload=data, checksum=digest(data))
        fd, temp = tempfile.mkstemp(dir=path.parent, prefix='.checkpoint-')
        try:
            with os.fdopen(fd, 'w') as out:
                json.dump(envelope, out, indent=2)
                out.flush()
                os.fsync(out.fileno())
            os.replace(temp, path)
            if os.name != 'nt':
                directory = os.open(path.parent, os.O_RDONLY)
                try: os.fsync(directory)
                finally: os.close(directory)
        finally:
            if os.path.exists(temp): os.unlink(temp)
        return data


def checkpoint(plan, run, manifest):
    return dict(generation=0, plan=copy.deepcopy(plan), run=copy.deepcopy(run),
                manifest=manifest, history=[])


def reconcile(saved, plan, observed):
    """Return a proposal. Preserve original evidence in history; never mutate source."""
    result = copy.deepcopy(saved)
    run = result['run']
    changed = sorted(k for k in set(saved['manifest']) | set(observed)
                     if saved['manifest'].get(k) != observed.get(k)
                     or (k in saved['manifest']) != (k in observed))
    plan_changed = digest(saved['plan']) != digest(plan)
    tasks = {t['id']: t for t in plan.get('tasks', [])}
    reasons = {}
    for tid, record in run.get('tasks', {}).items():
        if plan_changed:
            reasons[tid] = 'Plan content changed; replan and review affected work'
        elif changed:
            reasons[tid] = 'Source manifest changed; verify scope and candidate evidence'
        elif record.get('state') == 'running':
            reasons[tid] = 'Interrupted task; inspect workspace and agent before retry'
    # Conservative whole-run invalidation on any source drift avoids assuming
    # that path ownership captures runtime and cross-task dependencies.
    for tid, reason in reasons.items():
        record = run['tasks'][tid]
        result['history'].append(dict(task=tid, reason=reason, previous=copy.deepcopy(record)))
        record.update(state='blocked', reason=reason, checks=[], reviews=[])
        record.pop('candidate_revision', None)
        record.pop('integration_revision', None)
    if plan_changed or changed or reasons:
        result['history'].append(dict(final=copy.deepcopy(run.get('final', {})),
                                     previous_plan=copy.deepcopy(saved['plan'])))
        run['final'] = {'requirements': [], 'checks': [], 'reviews': []}
        run['status'] = 'blocked'
        issue = 'Recovery reconciliation required; inspect report before resuming'
        run['blockers'] = list(dict.fromkeys(run.get('blockers', []) + [issue]))
    # Preserve old baseline and plan binding until a reviewed replan is accepted.
    result['recovery'] = dict(changed_files=changed, plan_changed=plan_changed,
        blocked_tasks=sorted(reasons), added_tasks=sorted(set(tasks)-set(run.get('tasks', {}))),
        removed_tasks=sorted(set(run.get('tasks', {}))-set(tasks)),
        next_action='Inspect changes, reconcile side effects and revalidate before clearing blockers'
            if reasons or changed or plan_changed else 'Run execution gates; continue from recorded state')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('checkpoint', 'resume'):
        cmd = sub.add_parser(name)
        cmd.add_argument('--state', required=True)
        cmd.add_argument('--plan', required=True)
        cmd.add_argument('--root', required=True)
        cmd.add_argument('--manifest', required=True, help='JSON array of relative file paths')
        if name == 'checkpoint':
            cmd.add_argument('--run', required=True)
            cmd.add_argument('--expected-generation', required=True, type=int)
    args = parser.parse_args()
    plan = json.loads(Path(args.plan).read_text())
    manifest = fingerprint(args.root, json.loads(Path(args.manifest).read_text()))
    if args.command == 'checkpoint':
        run = json.loads(Path(args.run).read_text())
        data = checkpoint(plan, run, manifest)
        if Path(args.state).exists():
            old = load(args.state)
            data['history'] = old.get('history', []) + [dict(previous_run=old['run'], previous_plan=old['plan'], previous_manifest=old['manifest'])]
        data = save(args.state, data, args.expected_generation)
        print(json.dumps({'generation': data['generation']}))
    else:
        print(json.dumps(reconcile(load(args.state), plan, manifest), indent=2))


if __name__ == '__main__':
    try: main()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SystemExit('Recovery failed: ' + str(exc))
