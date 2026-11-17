"""Plan structure, provenance, and live review bindings.

These checks validate claims and freshness, not the truth of evidence or the
independence of a reviewer. Legacy records retain their original gate contract.
"""
import hashlib
import json
import re
from collections import deque
from pathlib import Path, PurePosixPath

SCHEMA_VERSION = 2
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
HASH = re.compile(r"^[a-f0-9]{64}$")
MARKER = re.compile(r"<!-- (/?)riff:generated:([a-z]+) -->")


def load(path):
    def invalid_constant(value):
        raise ValueError('Nonfinite JSON number: ' + value)
    value = json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=invalid_constant)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def simulated(value):
    if isinstance(value, dict):
        return value.get('simulated') is True or value.get('simulation') is True or any(simulated(v) for v in value.values())
    return isinstance(value, list) and any(simulated(v) for v in value)


def plan_digest(plan):
    """Bind substantive JSON without circularly binding review records."""
    return digest({k: v for k, v in plan.items() if k not in
                   {"reviews", "status", "review_history", "presentation"}})


def new_fields():
    return dict(schema_version=2, requirement_details=[], acceptance_checks=[],
                decisions=[], evidence=[], reports=[], reviewed_artifacts=["plan.md"],
                source_manifest={}, behavior_config={}, behavior_provenance={})


def relative_file(root, name):
    """Resolve a portable file path, rejecting escapes and symlink components."""
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        raise ValueError(f"Unsafe relative path: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in ("..", ".") for part in name.split("/")):
        raise ValueError(f"Unsafe relative path: {name}")
    root = Path(root).resolve()
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Symlink is not an authoritative file: {name}")
    if not current.resolve().is_relative_to(root) or current.resolve() == root:
        raise ValueError(f"Path escapes root: {name}")
    return current


def _strings(value, label, errors):
    if not isinstance(value, list) or any(not isinstance(v, str) or not v for v in value):
        errors.append(label + " must be an array of nonempty strings")
        return []
    if len(value) != len(set(value)):
        errors.append(label + " contains duplicates")
    return value


def _objects(value, label, errors, strict=True):
    if not isinstance(value, list) or any(not isinstance(v, dict) for v in value):
        errors.append(label + " must be an array of objects")
        return []
    result = {}
    for item in value:
        key = item.get("id")
        if not isinstance(key, str) or not key or (strict and not ID.fullmatch(key)):
            errors.append(label + ": invalid or missing id")
        elif key in result:
            errors.append(label + ": duplicate id " + key)
        else:
            result[key] = item
    return result


def graph_errors(plan):
    errors = []
    tasks = _objects(plan.get("tasks", []), "tasks", errors, plan.get('schema_version', 1) == 2)
    if not isinstance(tasks, dict):
        return errors
    graph = {}
    children = {key: [] for key in tasks}
    for key, task in tasks.items():
        graph[key] = _strings(task.get("dependencies", []), key + ".dependencies", errors)
        for dep in graph[key]:
            if dep not in tasks:
                errors.append("Unknown dependency: " + dep)
            else:
                children[dep].append(key)
    if errors:
        return errors
    counts = {key: len(deps) for key, deps in graph.items()}
    queue = deque(key for key, count in counts.items() if count == 0)
    visited = 0
    while queue:
        key = queue.popleft()
        visited += 1
        for child in children[key]:
            counts[child] -= 1
            if counts[child] == 0:
                queue.append(child)
    if visited != len(tasks):
        errors.append("Dependency cycle: " + ", ".join(key for key, count in counts.items() if count))
    return errors


def generated_sections(plan):
    errors = graph_errors(plan)
    if errors:
        raise ValueError("; ".join(errors))
    tasks = plan.get("tasks", [])
    rows = ["| Task | Objective | Depends on |", "| --- | --- | --- |"]
    graph = ["flowchart TD"]
    def cell(value):
        return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")
    # Internal Mermaid identifiers are generated, so task IDs can never become syntax.
    names = {task["id"]: "n" + str(i) for i, task in enumerate(tasks)}
    for task in tasks:
        key = task["id"]
        rows.append(f"| {cell(key)} | {cell(task.get('objective', ''))} | {cell(', '.join(task.get('dependencies', [])) or 'None')} |")
        label = ''.join(c if c.isalnum() or c in ' _.-' else '#' + str(ord(c)) + ';' for c in key)
        graph.append(f'    {names[key]}["{label}"]')
        for dep in task.get("dependencies", []):
            graph.append(f"    {names[dep]} --> {names[key]}")
    if not tasks:
        graph.append('    empty["No tasks recorded"]')
    return {"tasks": "\n".join(rows), "graph": "```mermaid\n" + "\n".join(graph) + "\n```"}


def authored_text(text, plan):
    sections = generated_sections(plan)
    matches = list(MARKER.finditer(text))
    # A malformed marker must not quietly become unbound generated content.
    if text.count("riff:generated:") != len(matches):
        raise ValueError("Malformed generated-section marker")
    seen, output, cursor, opened = set(), [], 0, None
    for match in matches:
        closing, name = match.groups()
        if name not in sections:
            raise ValueError("Unknown generated section: " + name)
        if not closing:
            if opened or name in seen:
                raise ValueError("Duplicate or nested generated section: " + name)
            output.append(text[cursor:match.start()])
            opened = (name, match.end())
            seen.add(name)
        else:
            if opened is None or opened[0] != name:
                raise ValueError("Unmatched generated section: " + name)
            body = text[opened[1]:match.start()].strip("\r\n")
            if body.replace("\r\n", "\n") != sections[name]:
                raise ValueError("Generated section differs from records: " + name)
            opened = None
            cursor = match.end()
    if opened:
        raise ValueError("Unclosed generated section: " + opened[0])
    output.append(text[cursor:])
    return "".join(output).replace("\r\n", "\n")


def authored_digest(task_dir, plan):
    paths = plan.get("reviewed_artifacts")
    if not isinstance(paths, list) or "plan.md" not in paths or any(not isinstance(p, str) for p in paths):
        raise ValueError("reviewed_artifacts must include plan.md")
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate reviewed_artifacts")
    bound = {}
    for name in paths:
        path = relative_file(task_dir, name)
        if name.endswith(".md"):
            content = authored_text(path.read_text(encoding="utf-8"), plan).encode("utf-8")
        else:
            content = path.read_bytes()
        bound[name] = hashlib.sha256(content).hexdigest()
    return digest(bound)


def live_errors(plan, context=None):
    if plan.get("schema_version", 1) == 1:
        return []
    if plan.get("schema_version") != 2:
        return ["Unsupported schema_version"]
    if not isinstance(context, dict) or not all(k in context for k in ("task_dir", "project", "effective_behavior")):
        return ["Live review inputs unavailable; supply task directory, project and effective behavior"]
    errors = []
    from . import reports
    for entry in plan.get('reports', []):
        if not isinstance(entry, dict):
            errors.append('Invalid report reference')
            continue
        try:
            report = reports.load(relative_file(context['task_dir'], entry.get('path')))
            if report.get('id') != entry.get('id') or report.get('kind') != entry.get('kind'):
                errors.append('Report identity differs from reference: ' + str(entry.get('id')))
            if report.get('status') == 'draft': errors.append('Referenced report is still draft: ' + str(entry.get('id')))
            if set(report.get('requirements', [])) - set(plan.get('requirements', [])):
                errors.append('Report references unknown requirements: ' + str(entry.get('id')))
            if set(report.get('decisions', [])) - {d['id'] for d in plan.get('decisions', [])}:
                errors.append('Report references unknown decisions: ' + str(entry.get('id')))
            if simulated(report): errors.append('Simulated report cannot qualify as evidence')
        except (OSError, ValueError, TypeError, KeyError) as exc:
            errors.append('Report unavailable or invalid: ' + str(exc))
    try:
        actual = authored_digest(context["task_dir"], plan)
        if actual != plan.get("authored_digest"):
            errors.append("Authored artifacts changed or digest missing; review current prose")
    except (OSError, ValueError, TypeError) as exc:
        errors.append("Authored artifacts unavailable: " + str(exc))
    behavior = plan.get("behavior_config")
    if not isinstance(behavior, dict) or digest(behavior) != plan.get("config_digest"):
        errors.append("Frozen behavioral configuration digest missing or invalid")
    elif digest(context["effective_behavior"]) != plan.get("config_digest"):
        errors.append("Effective behavioral configuration changed; replan required")
    manifest = context.get("source_manifest", plan.get("source_manifest"))
    if not isinstance(manifest, dict) or not manifest:
        errors.append("Source freshness unknown: source_manifest missing or empty")
    else:
        for name, expected in manifest.items():
            try:
                path = relative_file(context["project"], name)
                if expected is not None and (not isinstance(expected, str) or not HASH.fullmatch(expected)):
                    raise ValueError("Expected SHA256 digest or null")
                actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
                if path.exists() and not path.is_file():
                    raise ValueError("Manifest entry is not a file")
                if actual != expected:
                    errors.append("Source changed: " + name)
            except (OSError, ValueError, TypeError) as exc:
                errors.append("Source freshness unavailable for " + str(name) + ": " + str(exc))
    return errors


def validate(plan, context=None):
    try:
        return _validate(plan, context)
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        return ['Invalid plan record: ' + str(exc)]


def _validate(plan, context=None):
    if not isinstance(plan, dict):
        return ["Plan must be an object"]
    errors = []
    schema = plan.get("schema_version", 1)
    if type(schema) is not int or schema not in (1, 2):
        return ["Unsupported schema_version: " + str(schema)]
    errors.extend(graph_errors(plan))
    tasks = _objects(plan.get("tasks", []), "tasks", errors, schema == 2)
    requirements = _strings(plan.get("requirements", []), "requirements", errors)
    reviews = plan.get("reviews", [])
    if not isinstance(reviews, list) or any(not isinstance(r, dict) for r in reviews):
        errors.append("reviews must be an array of objects")
        reviews = []
    if plan.get("route") not in ("small", "standard", "complex", "critical"):
        errors.append("Invalid route")
    if plan.get("status") not in ("DRAFT", "BLOCKED", "CONDITIONAL", "READY"):
        errors.append("Invalid status")
    if not isinstance(tasks, dict):
        tasks = {}
    covered = set()
    for key, task in tasks.items():
        refs = _strings(task.get("requirements", []), key + ".requirements", errors)
        covered.update(refs)
        if schema == 2 and set(refs) - set(requirements):
            errors.append(key + ": unknown requirement reference")
    if schema == 2:
        _validate_v2(plan, tasks, requirements, errors)
    if plan.get("status") == "READY":
        if not tasks or not requirements:
            errors.append("Ready plan needs requirements and tasks")
        for key, task in tasks.items():
            for field in ("objective", "inputs", "scope", "outputs", "owner", "capability", "reviewer", "verification"):
                if not task.get(field):
                    errors.append(key + ": missing " + field)
        if set(requirements) - covered:
            errors.append("Uncovered requirements")
        if plan.get("blockers") or plan.get("unresolved_questions"):
            errors.append("Unresolved blockers or questions")
        if not plan.get("revision") or not plan.get("source_revision"):
            errors.append("Missing revision binding")
        def qualifying(review):
            base = (review.get("revision") == plan.get("revision") and
                    review.get("source_revision") == plan.get("source_revision") and
                    review.get("verdict") == "pass" and review.get("reviewer") and
                    not simulated(review) and
                    (plan.get("route") == "small" or review.get("independent") is True))
            if schema == 2:
                base = base and all(review.get(k) == v for k, v in {
                    "authored_digest": plan.get("authored_digest"),
                    "config_digest": plan.get("config_digest"),
                    "plan_digest": plan_digest(plan)}.items())
            return base
        if not any(qualifying(review) for review in reviews):
            errors.append("Missing current qualifying review")
        if simulated(plan): errors.append('Simulated evidence cannot qualify a READY plan')
        if schema == 2:
            errors.extend(live_errors(plan, context))
    return list(dict.fromkeys(errors))


def _validate_v2(plan, tasks, requirements, errors):
    if type(plan.get("revision")) is not int or plan["revision"] < 1:
        errors.append("revision must be a positive integer")
    if not isinstance(plan.get("behavior_config", {}), dict):
        errors.append("behavior_config must be an object")
    if not isinstance(plan.get("source_manifest", {}), dict):
        errors.append("source_manifest must be an object")
    collections = {key: _objects(plan.get(key, []), key, errors) for key in
                   ("requirement_details", "acceptance_checks", "decisions", "evidence", "reports")}
    collections = {key: value if isinstance(value, dict) else {} for key, value in collections.items()}
    def refs(item, field, allowed, required=False):
        values = _strings(item.get(field, []), item["id"] + "." + field, errors)
        if required and not values:
            errors.append(item["id"] + ": missing " + field)
        if set(values) - set(allowed):
            errors.append(item["id"] + ": unknown " + field + " reference")
        return values
    details = collections["requirement_details"]
    if set(details) - set(requirements):
        errors.append("Orphan requirement_details")
    if plan.get("status") == "READY" and set(requirements) - set(details):
        errors.append("Missing structured requirement descriptions")
    for item in details.values():
        if not isinstance(item.get("description"), str) or not item["description"].strip():
            errors.append(item["id"] + ": missing description")
        linked = refs(item, "acceptance_checks", collections["acceptance_checks"], plan.get("status") == "READY")
        for key in linked:
            check = collections["acceptance_checks"].get(key, {})
            if not isinstance(check.get("requirements", []), list) or item["id"] not in check.get("requirements", []):
                errors.append(item["id"] + ": acceptance check does not cover requirement")
    for item in collections["acceptance_checks"].values():
        refs(item, "requirements", requirements, True)
        for key in ("procedure", "expected"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(item["id"] + ": missing " + key)
        if plan.get("status") == "READY" and not any(
                isinstance(detail.get("acceptance_checks"), list) and
                item["id"] in detail["acceptance_checks"] for detail in details.values()):
            errors.append(item["id"] + ": orphan acceptance check")
    for item in collections["evidence"].values():
        for key in ("kind", "source"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(item["id"] + ": missing " + key)
        if item.get("classification") not in ("observed", "inferred", "assumed", "unresolved"):
            errors.append(item["id"] + ": invalid classification")
        if not item.get("revision") and not item.get("accessed"):
            errors.append(item["id"] + ": evidence needs revision or accessed date")
    for item in collections["decisions"].values():
        refs(item, "evidence", collections["evidence"])
        refs(item, "requirements", requirements)
        refs(item, "supersedes", collections["decisions"])
        if item.get("status") == "superseded":
            replacement = item.get("replaced_by")
            if not isinstance(replacement, str) or replacement not in collections["decisions"]:
                errors.append(item["id"] + ": superseded decision needs replaced_by")
    artifacts = _strings(plan.get("reviewed_artifacts", []), "reviewed_artifacts", errors)
    for item in collections["reports"].values():
        refs(item, "requirements", requirements)
        refs(item, "evidence", collections["evidence"])
        if item.get("kind") not in ("research", "debug", "replan"):
            errors.append(item["id"] + ": invalid report kind")
        if not isinstance(item.get("path"), str) or not item["path"]:
            errors.append(item["id"] + ": missing report path")
        elif plan.get("status") == "READY" and item["path"] not in artifacts:
            errors.append(item["id"] + ": report missing from reviewed_artifacts")
        if isinstance(item.get('path'), str):
            narrative = item.get('narrative', str(PurePosixPath(item['path']).with_suffix('.md')))
            if not item['path'].endswith('.json') or not isinstance(narrative, str) or not narrative.endswith('.md') or narrative == item['path']:
                errors.append(item['id'] + ': report needs distinct .json and .md artifact paths')
            if plan.get('status') == 'READY' and narrative not in artifacts:
                errors.append(item['id'] + ': report narrative missing from reviewed_artifacts')
