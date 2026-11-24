"""Single-file atomic writes with local locking and content compare-and-swap."""
import contextlib
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile

from . import records
from .records import new_fields


@contextlib.contextmanager
def _locked(path):
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise ValueError("Refusing symlink: " + str(parent))
    lock_path = path.with_name(path.name + ".lock")
    if lock_path.is_symlink():
        raise ValueError("Refusing symlink lock")
    with lock_path.open("a+b") as lock:
        if os.name == "nt":
            import msvcrt
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def atomic_json(path, value, expected_bytes=None, backup=False):
    """Write one JSON file. expected_bytes is the caller-observed preimage.

    No multi-file transaction is claimed. With backup=True the exact preimage
    survives before replacement, even if replacement fails.
    """
    path = Path(path)
    encoded = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    with _locked(path):
        original = path.read_bytes() if path.exists() else None
        if original != expected_bytes:
            raise ValueError("Concurrent edit: content changed; inspect and retry explicitly")
        saved = None
        if backup and original is not None:
            saved = path.with_name(path.name + ".backup-" + hashlib.sha256(original).hexdigest())
            if saved.is_symlink():
                raise ValueError("Refusing symlink backup")
            try:
                with saved.open("xb") as stream:
                    stream.write(original)
                    stream.flush()
                    os.fsync(stream.fileno())
            except FileExistsError:
                if saved.read_bytes() != original:
                    raise ValueError("Backup content does not match original")
        fd, temporary = tempfile.mkstemp(prefix=".riff-write-", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            # Recheck cooperative-unaware edits as close to replacement as possible.
            if (path.read_bytes() if path.exists() else None) != original:
                raise ValueError("Concurrent edit during write")
            os.replace(temporary, path)
        finally:
            Path(temporary).unlink(missing_ok=True)
        return saved


def _migration_guidance(plan, path, project, changed, applied):
    from . import config
    context = config.context(path, project) if project is not None else None
    ready = dict(plan, status='READY')
    gaps = records.validate(ready, context)
    execution = any((path.parent / name).exists() for name in ('run.json', 'checkpoint.json'))
    steps = []
    if changed and not applied:
        steps.append('Inspect this preview, then run riff migrate TASK --apply; add --manifest PATH to capture explicit source/configuration/authored bindings.')
    if gaps:
        steps.append('Complete the listed v2 requirements, acceptance checks and evidence gaps without inventing facts. Use riff plan --task TASK to continue planning.')
    steps.append('Obtain a current qualifying review before READY. Migration does not approve the plan or authorize implementation.')
    if execution:
        steps.append('Preserve run/checkpoint records and reconcile their old revision/baseline against the reviewed upgrade before resuming execution.')
    return dict(schema_version=plan.get('schema_version', 1), status=plan.get('status'),
                remaining_errors=gaps, source_paths=len(plan.get('source_manifest', {})),
                execution_reconciliation_required=execution, next_steps=steps)


def _bind_upgrade(plan, path, project, manifest):
    from . import config
    if project is None:
        raise ValueError('Explicit project is required for manifest binding')
    project = Path(project).resolve()
    if not path.resolve().is_relative_to(project):
        raise ValueError('Plan is outside project')
    if not isinstance(manifest, list) or not manifest or any(not isinstance(n, str) for n in manifest):
        raise ValueError('Source manifest must be a nonempty array of project-relative file names')
    protected = {path.resolve(), (path.parent / 'run.json').resolve(),
                 (path.parent / 'checkpoint.json').resolve()}
    fingerprints = {}
    for name in manifest:
        file = records.relative_file(project, name)
        if file in protected or file.name in ('plan.json.lock', 'run.json.lock', 'checkpoint.json.lock'):
            raise ValueError('Source manifest must not bind mutable plan/run/checkpoint state')
        if file.exists() and not file.is_file():
            raise ValueError('Source manifest entries must be files: ' + name)
        fingerprints[name] = hashlib.sha256(file.read_bytes()).hexdigest() if file.is_file() else None
    plan['source_manifest'] = fingerprints
    resolved = config.resolve(project, plan)
    plan.update(behavior_config=resolved['behavior'],
                behavior_provenance={k: resolved['provenance'][k] for k in resolved['behavior']},
                config_digest=resolved['digest'])
    plan['authored_digest'] = records.authored_digest(path.parent, plan)


def migrate(plan_path, apply=False, project=None, manifest=None):
    path = Path(plan_path)
    original = path.read_bytes()
    plan = json.loads(original)
    if not isinstance(plan, dict):
        raise ValueError("Plan must be an object")
    schema = plan.get("schema_version", 1)
    if type(schema) is not int or schema not in (1, 2):
        raise ValueError("Unsupported schema_version")
    if schema == 2:
        if manifest is not None:
            raise ValueError('Manifest binding is for legacy upgrades; use reviewed replan to change v2 bindings')
        return {"changed": False, "applied": False, "plan": plan, "backup": None,
                "guidance": _migration_guidance(plan, path, project, False, False)}
    revision = plan.get("revision", 0)
    if type(revision) is not int or revision < 0:
        raise ValueError("revision must be a nonnegative integer")
    upgraded = copy.deepcopy(plan)
    for key, value in new_fields().items():
        upgraded.setdefault(key, value)
    upgraded["schema_version"] = 2
    upgraded["revision"] = revision + 1
    upgraded["status"] = "DRAFT"
    history = upgraded.setdefault("review_history", [])
    if not isinstance(history, list):
        raise ValueError("review_history must be an array")
    history.append({"reason": "schema migration", "revision": revision,
                    "reviews": upgraded.get("reviews", [])})
    upgraded["reviews"] = []
    for field in ("authored_digest", "config_digest"):
        upgraded.pop(field, None)
    if manifest is not None:
        _bind_upgrade(upgraded, path, project, manifest)
    guidance = _migration_guidance(upgraded, path, project, True, bool(apply))
    backup_path = atomic_json(path, upgraded, original, backup=True) if apply else None
    return {"changed": True, "applied": bool(apply), "plan": upgraded,
            "backup": str(backup_path) if backup_path else None, "guidance": guidance}
