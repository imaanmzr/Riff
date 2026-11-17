"""Validate task-linked investigation reports; never execute recorded commands."""
import math
from .records import ID, load as load_object

KINDS = ("research", "debug", "replan")


def validate(report):
    if not isinstance(report, dict):
        return ["Report must be an object"]
    errors = []
    if type(report.get("schema_version")) is not int or report["schema_version"] != 1:
        errors.append("Unsupported report schema_version")
    if not isinstance(report.get("id"), str) or not ID.fullmatch(report["id"]):
        errors.append("Report needs a stable id")
    kind = report.get("kind")
    if kind not in KINDS:
        errors.append("Unknown report kind")
    if report.get("status") not in ("draft", "complete", "inconclusive"):
        errors.append("Invalid report status")
    finished = report.get("status") in ("complete", "inconclusive")

    def text(key, owner=report, needed=finished):
        value = owner.get(key)
        if not isinstance(value, str) or (needed and not value.strip()):
            errors.append(key + " must be " + ("nonempty " if needed else "") + "text")

    def array(key, owner=report, strings=False):
        value = owner.get(key)
        if not isinstance(value, list) or (strings and any(not isinstance(v, str) or not v for v in value)):
            errors.append(key + " must be an array" + (" of nonempty strings" if strings else ""))
            return []
        return value

    def objects(key):
        result = {}
        for value in array(key):
            if not isinstance(value, dict):
                errors.append(key + " entries must be objects")
                continue
            identity = value.get("id")
            if not isinstance(identity, str) or not ID.fullmatch(identity):
                errors.append(key + ": invalid id")
            elif identity in result:
                errors.append(key + ": duplicate id " + identity)
            else:
                result[identity] = value
        return result

    def references(key, owner, allowed):
        values = array(key, owner, strings=True)
        if len(values) != len(set(values)):
            errors.append(key + " contains duplicates")
        if set(values) - set(allowed):
            errors.append(owner.get("id", "entry") + ": unknown " + key + " reference")
        return values

    array("requirements", strings=True)
    array("decisions", strings=True)
    text("next_action")
    if kind == "research":
        for key in ("question", "scope", "success_criteria", "limits", "conclusion"):
            text(key)
        for key in ("alternatives", "uncertainty", "counterevidence"):
            array(key, strings=True)
        sources = objects("sources")
        for source in sources.values():
            text("source", source, True)
            if not source.get("revision") and not source.get("accessed"):
                errors.append(source["id"] + ": source needs revision or accessed date")
        claims = objects("claims")
        for claim in claims.values():
            text("text", claim, True)
            if claim.get("classification") not in ("observed", "inferred", "assumed", "unresolved"):
                errors.append(claim["id"] + ": invalid classification")
            refs = references("sources", claim, sources)
            if claim.get("classification") == "observed" and not refs:
                errors.append(claim["id"] + ": observed claim requires a source")
        if finished and not claims:
            errors.append("Finished research needs claims, including unresolved claims when inconclusive")
    elif kind == "debug":
        text("expected")
        text("actual")
        if not isinstance(report.get("environment"), dict):
            errors.append("environment must be an object")
        evidence = objects("evidence")
        for item in evidence.values():
            text("source", item, True)
            if not item.get("revision") and not item.get("accessed"):
                errors.append(item["id"] + ": evidence needs revision or accessed date")
        for reproduction in objects("reproductions").values():
            command = array("command", reproduction, strings=True)
            if not command:
                errors.append(reproduction["id"] + ": command cannot be empty")
            text("cwd", reproduction, True)
            if reproduction.get("exit_code") is not None and type(reproduction["exit_code"]) is not int:
                errors.append(reproduction["id"] + ": exit_code must be integer or null")
            if type(reproduction.get("timed_out")) is not bool:
                errors.append(reproduction["id"] + ": timed_out must be boolean")
            duration = reproduction.get("duration_seconds")
            if type(duration) not in (int, float) or not math.isfinite(duration) or duration < 0:
                errors.append(reproduction["id"] + ": duration_seconds must be nonnegative")
            for key in ("stdout", "stderr"):
                text(key, reproduction, False)
            references("evidence", reproduction, evidence)
        for hypothesis in objects("hypotheses").values():
            text("text", hypothesis, True)
            if hypothesis.get("status") not in ("unresolved", "supported", "refuted"):
                errors.append(hypothesis["id"] + ": invalid hypothesis status")
            references("evidence", hypothesis, evidence)
        references("causal_evidence", report, evidence)
        if report.get("proposed_fix") is not None:
            text("proposed_fix", needed=False)
        array("regression_checks", strings=True)
        if report.get("status") == "complete" and not report.get("causal_evidence"):
            errors.append("Complete diagnosis needs causal_evidence; otherwise record inconclusive")
    elif kind == "replan":
        text("reason")
        text("source_revision")
        before, after = report.get("baseline_revision"), report.get("target_revision")
        if type(before) is not int or before < 1:
            errors.append("baseline_revision must be positive")
        if type(after) is not int or type(before) is not int or after <= before:
            errors.append("target_revision must exceed baseline_revision")
        for key in ("superseded_decisions", "affected_tasks", "invalidated_reviews", "changes"):
            array(key, strings=True)
        text("snapshot")
        text("reconciliation", needed=False)
    return list(dict.fromkeys(errors))


def load(path):
    report = load_object(path)
    errors = validate(report)
    if errors:
        raise ValueError("Invalid report: " + "; ".join(errors))
    return report
