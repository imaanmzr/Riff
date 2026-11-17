"""Single-file atomic writes with local locking and content compare-and-swap."""
import contextlib
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile

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


def migrate(plan_path, apply=False):
    path = Path(plan_path)
    original = path.read_bytes()
    plan = json.loads(original)
    if not isinstance(plan, dict):
        raise ValueError("Plan must be an object")
    schema = plan.get("schema_version", 1)
    if type(schema) is not int or schema not in (1, 2):
        raise ValueError("Unsupported schema_version")
    if schema == 2:
        return {"changed": False, "applied": False, "plan": plan, "backup": None}
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
    backup_path = atomic_json(path, upgraded, original, backup=True) if apply else None
    return {"changed": True, "applied": bool(apply), "plan": upgraded,
            "backup": str(backup_path) if backup_path else None}
