"""Evidence integrity, provenance, freshness, and independence controls.

Evidence validation is deliberately separated from agent reasoning. Synthetic/demo
material may be used to exercise the architecture, but is never decision-usable.
"""

from datetime import datetime, timezone
import hashlib
import re
from typing import Any, Dict, List


DEFAULT_MAX_AGE_SECONDS = 24 * 60 * 60


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _source_identity(evidence: Dict[str, Any]) -> str:
    provenance = evidence.get("provenance") or {}
    return _normalize(
        provenance.get("publisher")
        or provenance.get("source_id")
        or evidence.get("source")
    )


def claim_fingerprint(evidence: Dict[str, Any]) -> str:
    """Create a stable fingerprint for grouping materially identical claims."""
    payload = f"{_normalize(evidence.get('claim'))}|{_source_identity(evidence)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def validate_evidence(evidence: Dict[str, Any], now: datetime | None = None,
                      max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS) -> Dict[str, Any]:
    """Return a deterministic validation report for one evidence item."""
    now = now or datetime.now(timezone.utc)
    errors: List[str] = []
    warnings: List[str] = []

    for field in ("evidence_id", "source", "claim"):
        if not evidence.get(field):
            errors.append(f"Missing required evidence field: {field}.")

    observed = _parse_timestamp(evidence.get("observed_at"))
    retrieved = _parse_timestamp(evidence.get("retrieved_at"))
    if evidence.get("observed_at") and observed is None:
        errors.append("observed_at is not a valid timestamp.")
    if evidence.get("retrieved_at") and retrieved is None:
        errors.append("retrieved_at is not a valid timestamp.")
    if observed and retrieved and retrieved < observed:
        errors.append("retrieved_at precedes observed_at.")
    if retrieved and retrieved > now:
        errors.append("retrieved_at is in the future.")
    if observed and observed > now:
        errors.append("observed_at is in the future.")

    provenance = evidence.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("Evidence provenance is missing or invalid.")
    else:
        if provenance.get("type") == "synthetic_demo":
            errors.append("Synthetic demo evidence is not decision-usable.")
        if provenance.get("point_in_time") is not True:
            warnings.append("Point-in-time provenance is not explicitly established.")

    freshness_seconds = None
    reference_time = observed or retrieved
    if reference_time:
        freshness_seconds = max(0.0, (now - reference_time).total_seconds())
        if freshness_seconds > max_age_seconds:
            errors.append(f"Evidence is stale ({round(freshness_seconds)} seconds old).")

    return {
        "evidence_id": evidence.get("evidence_id"),
        "valid": not errors,
        "decision_usable": not errors,
        "errors": errors,
        "warnings": warnings,
        "freshness_seconds": freshness_seconds,
        "freshness_limit_seconds": max_age_seconds,
        "claim_fingerprint": claim_fingerprint(evidence),
        "source_identity": _source_identity(evidence),
    }


def validate_agent_evidence(agent: Dict[str, Any], now: datetime | None = None,
                            max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS) -> Dict[str, Any]:
    """Validate all evidence attached to an agent without altering its reasoning."""
    evidence = agent.get("evidence") or []
    reports = [validate_evidence(item, now=now, max_age_seconds=max_age_seconds) for item in evidence]
    usable = bool(reports) and all(report["decision_usable"] for report in reports)
    corroboration = corroborate_evidence(evidence, now=now, max_age_seconds=max_age_seconds)
    return {
        "agent_id": agent.get("agent_id"),
        "evidence_count": len(reports),
        "usable": usable,
        "reports": reports,
        "corroboration": corroboration,
        "status": "verified" if usable else ("missing" if not reports else "blocked"),
    }


def corroborate_evidence(evidence: List[Dict[str, Any]], now: datetime | None = None,
                         max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS) -> Dict[str, Any]:
    """Measure corroboration without treating syndication as independent evidence."""
    groups: Dict[str, List[Dict[str, Any]]] = {}
    source_ids = set()
    dependent_ids: List[str] = []
    usable_ids: List[str] = []

    for item in evidence:
        report = validate_evidence(item, now=now, max_age_seconds=max_age_seconds)
        if not report["decision_usable"]:
            continue
        usable_ids.append(item.get("evidence_id"))
        source_ids.add(report["source_identity"])
        groups.setdefault(_normalize(item.get("claim")), []).append(item)
        parent_id = (item.get("provenance") or {}).get("parent_evidence_id")
        if parent_id:
            dependent_ids.append(item.get("evidence_id"))

    independent_ids = [eid for eid in usable_ids if eid not in dependent_ids]
    independent_sources = set()
    for item in evidence:
        if item.get("evidence_id") in independent_ids:
            independent_sources.add(_source_identity(item))

    return {
        "claim_group_count": len(groups),
        "unique_source_count": len(source_ids),
        "independent_source_count": len(independent_sources),
        "independent_evidence_count": len(independent_ids),
        "usable_evidence_count": len(usable_ids),
        "dependent_evidence_ids": dependent_ids,
        "independence_rule": "Explicit parent/syndication relationships are not counted as independent corroboration.",
    }


def apply_evidence_gate(agents: List[Dict[str, Any]], now: datetime | None = None,
                        max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Attach validation results and force unusable evidence to NO_DATA."""
    gated: List[Dict[str, Any]] = []
    validations: List[Dict[str, Any]] = []
    for original in agents:
        agent = dict(original)
        validation = validate_agent_evidence(agent, now=now, max_age_seconds=max_age_seconds)
        agent["evidence_validation"] = validation
        if not validation["usable"] and agent.get("direction") != "NO_DATA":
            agent["pre_evidence_direction"] = agent.get("direction")
            agent["direction"] = "NO_DATA"
            agent["evidence_gate"] = "BLOCKED"
        else:
            agent["evidence_gate"] = "PASSED"
        gated.append(agent)
        validations.append(validation)
    return gated, validations
