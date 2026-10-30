"""Deterministic MITRE identifiers and names from the packaged reference cards.

The cards deliberately list parent techniques only. Unknown IDs, tactics,
data sources and unlisted sub-techniques are not authoritative annotations.
Refreshing the cards updates both the model's catalogue and this validator.
"""

from __future__ import annotations

import re
from functools import cache
from importlib.resources import files
from types import MappingProxyType
from typing import Any

_ENTRY = re.compile(r"^- \*\*((?:AML\.)?T\d{4}(?:\.\d{3})?)\*\* — (.+)$", re.MULTILINE)


@cache
def technique_catalog() -> MappingProxyType[str, str]:
    """Load exact IDs and canonical names; fail closed on broken package data."""
    catalog: dict[str, str] = {}
    package = files("stride_gpt.core.prompts.threat_model")
    for name in ("mitre_enterprise.md", "mitre_atlas.md"):
        entries = _ENTRY.findall((package / name).read_text(encoding="utf-8"))
        if not entries:
            raise ValueError(f"Packaged MITRE catalogue has no techniques: {name}")
        for technique_id, title in entries:
            title = title.strip()
            if technique_id in catalog and catalog[technique_id] != title:
                raise ValueError(f"Conflicting packaged MITRE name for {technique_id}")
            catalog[technique_id] = title
    return MappingProxyType(catalog)


def normalize_techniques(value: Any) -> list[tuple[str, str]]:
    """Keep catalogue members once, in input order, replacing model names."""
    entries = [value] if isinstance(value, str) else value if isinstance(value, list) else []
    catalog = technique_catalog()
    accepted: dict[str, str] = {}
    for entry in entries:
        if isinstance(entry, dict):
            candidates = [entry.get("id")]
        elif isinstance(entry, str):
            candidates = entry.split(",")
        else:
            continue
        for candidate in candidates:
            if isinstance(candidate, str) and (technique_id := candidate.strip()) in catalog:
                accepted[technique_id] = catalog[technique_id]
    return list(accepted.items())


def normalize_threat_mitre(threat: dict[str, Any]) -> dict[str, Any]:
    """Return a copy safe for JSON, checkpoints and non-rendering consumers."""
    result = dict(threat)
    if "MITRE_ATTACK" in result:
        result["MITRE_ATTACK"] = [
            {"id": technique_id, "name": name}
            for technique_id, name in normalize_techniques(result["MITRE_ATTACK"])
        ]
    return result
