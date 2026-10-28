"""The security control catalogue and its deterministic framework mappings.

The catalogue (``catalog.toml``, packaged data) lists security controls —
identity, data protection, network, logging, application security, AI and
agentic controls, AI governance — each mapped to AIUC-1, ISO/IEC 42001, the
EU AI Act and ISO/IEC 27001.

The split of responsibilities is the point of this module. The model reads a
reference card generated from the catalogue and tags each threat with control
IDs (``CONTROLS``). Everything downstream of that choice — which framework
requirements a threat bears on — is a lookup here, so a report can never
contain a clause number the model made up. It's the same anti-hallucination
contract the MITRE cards use, moved from the prompt into code.
"""

from __future__ import annotations

import re
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass
from functools import cache, cached_property
from importlib.resources import files
from typing import Any

_PACKAGE = "stride_gpt.core.controls"
_CATALOG_FILE = "catalog.toml"

STRIDE_LETTERS = ("S", "T", "R", "I", "D", "E")
STRIDE_NAMES = {
    "S": "Spoofing",
    "T": "Tampering",
    "R": "Repudiation",
    "I": "Information Disclosure",
    "D": "Denial of Service",
    "E": "Elevation of Privilege",
}

# Domains whose controls only make sense for an AI system. A report that uses
# one is about an AI system, whatever else it contains.
AI_DOMAINS = frozenset({"AI", "AGT", "GOV"})

_ID_SHAPE = re.compile(r"^[A-Z]{2,3}-\d{2}$")


class CatalogError(ValueError):
    """The packaged catalogue is malformed. Raised with every problem found."""


# ---------------------------------------------------------------------------
# Catalogue model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Framework:
    """A framework the catalogue maps to, with its registry of valid references."""

    key: str
    name: str
    full_name: str
    version: str
    url: str
    ai_specific: bool
    note: str
    # (reference, title) pairs in declaration order — the order reports use.
    refs: tuple[tuple[str, str], ...]

    @cached_property
    def _titles(self) -> dict[str, str]:
        return dict(self.refs)

    def title(self, ref: str) -> str:
        return self._titles.get(ref, "")

    def has_ref(self, ref: str) -> bool:
        return ref in self._titles


@dataclass(frozen=True)
class Domain:
    key: str
    title: str
    card: str
    summary: str


@dataclass(frozen=True)
class Card:
    """A reference card the catalogue is rendered into."""

    name: str
    title: str
    when_to_load: str
    intro: str
    example: tuple[str, ...]


@dataclass(frozen=True)
class Control:
    id: str
    domain: str
    name: str
    objective: str
    guidance: tuple[str, ...]
    stride: tuple[str, ...]
    mitigates: tuple[str, ...]
    references: tuple[str, ...]
    # (framework key, references) pairs; frameworks with no mapping are absent.
    mappings: tuple[tuple[str, tuple[str, ...]], ...]

    def refs_for(self, framework: str) -> tuple[str, ...]:
        for key, refs in self.mappings:
            if key == framework:
                return refs
        return ()


@dataclass(frozen=True)
class Catalog:
    version: str
    cards: tuple[Card, ...]
    owasp: tuple[tuple[str, str], ...]
    frameworks: tuple[Framework, ...]
    domains: tuple[Domain, ...]
    controls: tuple[Control, ...]

    @cached_property
    def _by_id(self) -> dict[str, Control]:
        return {c.id: c for c in self.controls}

    @cached_property
    def _order(self) -> dict[str, int]:
        return {c.id: n for n, c in enumerate(self.controls)}

    def control(self, control_id: str) -> Control | None:
        return self._by_id.get(control_id)

    def position(self, control_id: str) -> int:
        """Catalogue order of a control, for stable sorting."""
        return self._order.get(control_id, len(self._order))

    def framework(self, key: str) -> Framework | None:
        return next((f for f in self.frameworks if f.key == key), None)

    def domain(self, key: str) -> Domain | None:
        return next((d for d in self.domains if d.key == key), None)

    def card(self, name: str) -> Card | None:
        return next((c for c in self.cards if c.name == name), None)

    def controls_for_card(self, card: str) -> list[Control]:
        keys = {d.key for d in self.domains if d.card == card}
        return [c for c in self.controls if c.domain in keys]

    def owasp_title(self, code: str) -> str:
        return dict(self.owasp).get(code, "")

    @property
    def control_ids(self) -> list[str]:
        return [c.id for c in self.controls]

    @cached_property
    def id_pattern(self) -> re.Pattern[str]:
        """Matches a control ID in free text, tolerating a missing zero pad."""
        prefixes = "|".join(sorted((d.key for d in self.domains), key=len, reverse=True))
        return re.compile(rf"\b({prefixes})-(\d{{1,3}})\b")


@cache
def load_catalog() -> Catalog:
    """Load and validate the packaged catalogue. Cached: it's read-only data."""
    text = (files(_PACKAGE) / _CATALOG_FILE).read_text(encoding="utf-8")
    return parse_catalog(tomllib.loads(text))


def parse_catalog(data: dict[str, Any]) -> Catalog:
    """Build a :class:`Catalog` from parsed TOML, validating every reference.

    Collects every problem before raising so a bad edit is fixed in one pass.
    Public so tests can feed it deliberately broken data.
    """
    errors: list[str] = []

    cards = tuple(
        Card(
            name=name,
            title=_str(body, "title", f"card {name}", errors),
            when_to_load=_str(body, "when_to_load", f"card {name}", errors),
            intro=_str(body, "intro", f"card {name}", errors),
            example=tuple(_str_list(body, "example", f"card {name}", errors)),
        )
        for name, body in _table(data, "cards", errors).items()
    )
    owasp = tuple((str(k), str(v)) for k, v in _table(data, "owasp", errors).items())

    frameworks = tuple(
        Framework(
            key=key,
            name=_str(body, "name", f"framework {key}", errors),
            full_name=_str(body, "full_name", f"framework {key}", errors),
            version=_str(body, "version", f"framework {key}", errors),
            url=_str(body, "url", f"framework {key}", errors),
            ai_specific=bool(body.get("ai_specific", False)),
            note=_str(body, "note", f"framework {key}", errors),
            refs=tuple((str(r), str(t)) for r, t in (body.get("refs") or {}).items()),
        )
        for key, body in _table(data, "frameworks", errors).items()
    )
    domains = tuple(
        Domain(
            key=key,
            title=_str(body, "title", f"domain {key}", errors),
            card=_str(body, "card", f"domain {key}", errors),
            summary=_str(body, "summary", f"domain {key}", errors),
        )
        for key, body in _table(data, "domains", errors).items()
    )

    raw_controls = data.get("controls")
    if not isinstance(raw_controls, list) or not raw_controls:
        errors.append("catalogue has no [[controls]]")
        raw_controls = []
    controls = tuple(_parse_control(raw, errors) for raw in raw_controls)

    catalog = Catalog(
        version=str(data.get("catalog_version") or ""),
        cards=cards,
        owasp=owasp,
        frameworks=frameworks,
        domains=domains,
        controls=controls,
    )
    errors.extend(_cross_check(catalog))
    if not catalog.version:
        errors.append("catalog_version is missing")
    if errors:
        raise CatalogError("Invalid control catalogue:\n  " + "\n  ".join(errors))
    return catalog


def _parse_control(raw: Any, errors: list[str]) -> Control:
    if not isinstance(raw, dict):
        errors.append(f"control entry is not a table: {raw!r}")
        raw = {}
    cid = str(raw.get("id") or "?")
    where = f"control {cid}"
    mappings_raw = raw.get("mappings") or {}
    if not isinstance(mappings_raw, dict):
        errors.append(f"{where}: mappings must be a table")
        mappings_raw = {}
    mappings = tuple(
        (str(fw), tuple(_str_list(mappings_raw, fw, where, errors, required=False)))
        for fw in mappings_raw
    )
    return Control(
        id=cid,
        domain=_str(raw, "domain", where, errors),
        name=_str(raw, "name", where, errors),
        objective=_str(raw, "objective", where, errors),
        guidance=tuple(_str_list(raw, "guidance", where, errors)),
        stride=tuple(_str_list(raw, "stride", where, errors, required=False)),
        mitigates=tuple(_str_list(raw, "mitigates", where, errors, required=False)),
        references=tuple(_str_list(raw, "references", where, errors, required=False)),
        mappings=tuple((fw, refs) for fw, refs in mappings if refs),
    )


def _cross_check(catalog: Catalog) -> list[str]:
    """Referential integrity: every ID, domain, card and mapping must resolve."""
    card_names = {c.name for c in catalog.cards}
    ids = [c.id for c in catalog.controls]
    errors = [
        f"framework {f.key}: refs registry is empty" for f in catalog.frameworks if not f.refs
    ]
    errors.extend(
        f"domain {d.key}: unknown card {d.card!r}"
        for d in catalog.domains
        if d.card not in card_names
    )
    errors.extend(f"control {cid}: duplicate id" for cid in sorted(set(ids)) if ids.count(cid) > 1)
    for control in catalog.controls:
        errors.extend(_control_problems(catalog, control))
    errors.extend(
        f"card {card.name}: example id {cid!r} is not in the catalogue"
        for card in catalog.cards
        for cid in card.example
        if cid not in ids
    )
    return errors


def _control_problems(catalog: Catalog, control: Control) -> list[str]:
    where = f"control {control.id}"
    problems: list[str] = []
    if not _ID_SHAPE.match(control.id):
        problems.append(f"{where}: id must look like 'IAM-01'")
    if catalog.domain(control.domain) is None:
        problems.append(f"{where}: unknown domain {control.domain!r}")
    elif not control.id.startswith(control.domain + "-"):
        problems.append(f"{where}: id prefix does not match domain {control.domain}")
    owasp_codes = {code for code, _title in catalog.owasp}
    problems.extend(
        f"{where}: unknown STRIDE letter {s!r}" for s in control.stride if s not in STRIDE_LETTERS
    )
    problems.extend(
        f"{where}: unknown OWASP code {code!r}"
        for code in control.mitigates
        if code not in owasp_codes
    )
    for fw_key, refs in control.mappings:
        framework = catalog.framework(fw_key)
        if framework is None:
            problems.append(f"{where}: unknown framework {fw_key!r}")
            continue
        problems.extend(
            f"{where}: {fw_key} has no reference {ref!r}"
            for ref in refs
            if not framework.has_ref(ref)
        )
        if len(set(refs)) != len(refs):
            problems.append(f"{where}: duplicate {fw_key} reference")
    return problems


def _table(data: dict[str, Any], key: str, errors: list[str]) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict) or not value:
        errors.append(f"[{key}] is missing or empty")
        return {}
    return value


def _str(body: Any, key: str, where: str, errors: list[str]) -> str:
    value = body.get(key) if isinstance(body, dict) else None
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{where}: {key} must be a non-empty string")
        return ""
    return value.strip()


def _str_list(
    body: Any, key: str, where: str, errors: list[str], *, required: bool = True
) -> list[str]:
    value = body.get(key) if isinstance(body, dict) else None
    if value is None and not required:
        return []
    if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
        errors.append(f"{where}: {key} must be a list of non-empty strings")
        return []
    if required and not value:
        errors.append(f"{where}: {key} must not be empty")
    return [v.strip() for v in value]


# ---------------------------------------------------------------------------
# Reading CONTROLS off a threat
# ---------------------------------------------------------------------------


def split_control_ids(value: Any) -> tuple[list[str], list[str]]:
    """Split a threat's ``CONTROLS`` value into known IDs and rejects.

    Accepts the shapes models produce: the canonical list of IDs, a comma-
    separated string, list entries with a name attached (``"IAM-05 (JWT)"``),
    lowercase or unpadded IDs (``"iam-5"``), and ``{"id": ...}`` objects.
    Known IDs come back canonical, deduplicated, in the order given. Rejects
    are what the agent loop reports back to the model so it can correct
    itself: IDs that aren't in the catalogue, and entries with no ID at all.
    """
    if value is None or value == "" or value == []:
        return [], []
    if isinstance(value, list):
        entries: list[Any] = value
    elif isinstance(value, str | dict):
        entries = [value]
    else:
        return [], [str(value)[:40]]

    catalog = load_catalog()
    known: list[str] = []
    rejected: list[str] = []
    for entry in entries:
        text = entry.get("id") if isinstance(entry, dict) else entry
        if not isinstance(text, str):
            rejected.append(str(text)[:40])
            continue
        parts = [p for p in text.split(",") if p.strip()]
        for part in parts:
            matches = catalog.id_pattern.findall(part.upper())
            if not matches:
                rejected.append(part.strip()[:40])
                continue
            for prefix, number in matches:
                cid = f"{prefix}-{int(number):02d}"
                if catalog.control(cid) is None:
                    rejected.append(cid)
                elif cid not in known:
                    known.append(cid)
    return known, rejected


def normalize_control_ids(value: Any) -> list[str]:
    """The known catalogue IDs in a ``CONTROLS`` value — the single reading
    every renderer uses, so markdown, HTML, SARIF and JSON can't disagree."""
    return split_control_ids(value)[0]


def keep_known_controls(threat: Any) -> None:
    """Rewrite a threat's ``CONTROLS`` in place to its known, canonical IDs.

    Drops the key when nothing valid remains. Renderers filter anyway; this
    is for what gets saved or exported, which downstream tools import, so it
    shouldn't carry an ID the model invented.
    """
    if not isinstance(threat, dict) or "CONTROLS" not in threat:
        return
    known = normalize_control_ids(threat["CONTROLS"])
    if known:
        threat["CONTROLS"] = known
    else:
        del threat["CONTROLS"]


def controls_mitigating(code: str) -> list[Control]:
    """Catalogue controls that declare they address an OWASP risk code."""
    return [c for c in load_catalog().controls if code in c.mitigates]


def has_ai_scope(threats: Iterable[Any]) -> bool:
    """Whether a set of threats concerns an AI system.

    AI frameworks (AIUC-1, ISO/IEC 42001, EU AI Act) are only relevant when it
    does: a TLS gap in a plain web app bears on ISO/IEC 27001, not on the EU
    AI Act. The signals are the ones the AI reference cards add — OWASP LLM or
    ASI codes, an insider-threat category, an ATLAS technique — or an AI,
    agentic or governance control.
    """
    for threat in threats:
        if not isinstance(threat, dict):
            continue
        if threat.get("OWASP_LLM") or threat.get("OWASP_ASI") or threat.get("INSIDER_CATEGORY"):
            return True
        if _mentions_atlas(threat.get("MITRE_ATTACK")):
            return True
        if any(cid.split("-")[0] in AI_DOMAINS for cid in normalize_control_ids(threat.get("CONTROLS"))):
            return True
    return False


def framework_refs(control_ids: Iterable[str], *, ai_scope: bool) -> dict[str, list[str]]:
    """Framework references for a set of controls, keyed by framework key.

    Per-threat counterpart of :func:`compliance_summary`, for SARIF results.
    AI frameworks are left out unless ``ai_scope`` — decide that once for the
    whole report with :func:`has_ai_scope`, so every result agrees with the
    report's summary.
    """
    catalog = load_catalog()
    controls = [c for cid in control_ids if (c := catalog.control(cid)) is not None]
    result: dict[str, list[str]] = {}
    for framework in catalog.frameworks:
        if framework.ai_specific and not ai_scope:
            continue
        wanted = {ref for c in controls for ref in c.refs_for(framework.key)}
        refs = [ref for ref, _title in framework.refs if ref in wanted]
        if refs:
            result[framework.key] = refs
    return result


def _mentions_atlas(value: Any) -> bool:
    entries = value if isinstance(value, list) else [value]
    for entry in entries:
        text = entry.get("id") if isinstance(entry, dict) else entry
        if isinstance(text, str) and "AML." in text.upper():
            return True
    return False


# ---------------------------------------------------------------------------
# Compliance summary
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ControlUse:
    control: Control
    threat_count: int


@dataclass(frozen=True)
class RefUse:
    """One framework reference, the recommended controls that address it, and
    how many threats those controls were recommended for."""

    ref: str
    title: str
    control_ids: tuple[str, ...]
    threat_count: int


@dataclass(frozen=True)
class FrameworkCoverage:
    framework: Framework
    refs: tuple[RefUse, ...]


@dataclass(frozen=True)
class ComplianceSummary:
    catalog_version: str
    ai_scope: bool
    controls: tuple[ControlUse, ...]
    frameworks: tuple[FrameworkCoverage, ...]

    @property
    def omitted_frameworks(self) -> list[Framework]:
        """AI frameworks left out because no threat concerns an AI system."""
        if self.ai_scope:
            return []
        return [f for f in load_catalog().frameworks if f.ai_specific]

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable form for report JSON and SARIF consumers."""
        catalog = load_catalog()
        return {
            "catalog_version": self.catalog_version,
            "ai_scope": self.ai_scope,
            "controls": [
                {
                    "id": use.control.id,
                    "name": use.control.name,
                    "domain": use.control.domain,
                    "domain_title": (catalog.domain(use.control.domain) or _NO_DOMAIN).title,
                    "threat_count": use.threat_count,
                    "mappings": {fw: list(refs) for fw, refs in use.control.mappings},
                }
                for use in self.controls
            ],
            "frameworks": [
                {
                    "key": cov.framework.key,
                    "name": cov.framework.name,
                    "full_name": cov.framework.full_name,
                    "version": cov.framework.version,
                    "refs": [
                        {
                            "ref": ref.ref,
                            "title": ref.title,
                            "controls": list(ref.control_ids),
                            "threat_count": ref.threat_count,
                        }
                        for ref in cov.refs
                    ],
                }
                for cov in self.frameworks
            ],
            "omitted_frameworks": [f.name for f in self.omitted_frameworks],
        }


_NO_DOMAIN = Domain(key="", title="", card="", summary="")


def compliance_summary(threats: Iterable[Any]) -> ComplianceSummary | None:
    """Roll a report's threats up into controls and framework references.

    Returns None when no threat carries a known control, so renderers can
    skip the section entirely — reports from runs that never loaded a
    controls card look exactly as they did before the catalogue existed.

    Every number here is derived from the threats' ``CONTROLS`` and the
    catalogue; nothing is read from a previously saved summary, so a live
    render and a re-render of saved JSON always agree.
    """
    catalog = load_catalog()
    threat_list = [t for t in threats if isinstance(t, dict)]
    per_threat = [normalize_control_ids(t.get("CONTROLS")) for t in threat_list]
    if not any(per_threat):
        return None

    threats_by_control: dict[str, set[int]] = {}
    for index, ids in enumerate(per_threat):
        for cid in ids:
            threats_by_control.setdefault(cid, set()).add(index)

    uses = sorted(
        (
            ControlUse(control, len(threats_by_control[cid]))
            for cid in threats_by_control
            if (control := catalog.control(cid)) is not None
        ),
        key=lambda use: (-use.threat_count, catalog.position(use.control.id)),
    )

    ai_scope = has_ai_scope(threat_list)
    coverage: list[FrameworkCoverage] = []
    for framework in catalog.frameworks:
        if framework.ai_specific and not ai_scope:
            continue
        controls_by_ref: dict[str, set[str]] = {}
        threats_by_ref: dict[str, set[int]] = {}
        for cid, indexes in threats_by_control.items():
            control = catalog.control(cid)
            if control is None:
                continue
            for ref in control.refs_for(framework.key):
                controls_by_ref.setdefault(ref, set()).add(cid)
                threats_by_ref.setdefault(ref, set()).update(indexes)
        refs = tuple(
            RefUse(
                ref=ref,
                title=title,
                control_ids=tuple(sorted(controls_by_ref[ref], key=catalog.position)),
                threat_count=len(threats_by_ref[ref]),
            )
            for ref, title in framework.refs
            if ref in controls_by_ref
        )
        coverage.append(FrameworkCoverage(framework, refs))

    return ComplianceSummary(
        catalog_version=catalog.version,
        ai_scope=ai_scope,
        controls=tuple(uses),
        frameworks=tuple(coverage),
    )


COMPLIANCE_ROW_FIELDS = (
    "threat_type",
    "scenario",
    "control_id",
    "control_name",
    "framework",
    "reference",
    "requirement",
)

# A spreadsheet treats a cell starting with one of these as a formula. Scenario
# text comes from a model and may have been steered by whoever wrote the
# application description, so exported cells are defused (OWASP CSV Injection).
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def spreadsheet_safe(value: Any) -> str:
    """Neutralise a value that a spreadsheet would evaluate as a formula."""
    text = "" if value is None else str(value)
    return "'" + text if text.startswith(_FORMULA_PREFIXES) else text


def compliance_rows(threats: Iterable[Any]) -> list[dict[str, str]]:
    """One row per (threat, control, framework reference), for CSV export.

    The flat shape GRC tools import. Applies the same AI-scope rule as
    :func:`compliance_summary`. A control with no reference in a framework
    still gets a row (empty reference) so no recommended control silently
    disappears from the export. Every value is passed through
    :func:`spreadsheet_safe`.
    """
    catalog = load_catalog()
    threat_list = [t for t in threats if isinstance(t, dict)]
    ai_scope = has_ai_scope(threat_list)
    frameworks = [f for f in catalog.frameworks if ai_scope or not f.ai_specific]
    rows: list[dict[str, str]] = []
    for threat in threat_list:
        for cid in normalize_control_ids(threat.get("CONTROLS")):
            control = catalog.control(cid)
            if control is None:
                continue
            base = {
                "threat_type": threat.get("Threat Type", ""),
                "scenario": threat.get("Scenario", ""),
                "control_id": control.id,
                "control_name": control.name,
            }
            for framework in frameworks:
                refs = control.refs_for(framework.key) or ("",)
                rows.extend(
                    {
                        key: spreadsheet_safe(value)
                        for key, value in {
                            **base,
                            "framework": framework.name,
                            "reference": ref,
                            "requirement": framework.title(ref),
                        }.items()
                    }
                    for ref in refs
                )
    return rows


__all__ = [
    "AI_DOMAINS",
    "COMPLIANCE_ROW_FIELDS",
    "STRIDE_LETTERS",
    "STRIDE_NAMES",
    "Card",
    "Catalog",
    "CatalogError",
    "ComplianceSummary",
    "Control",
    "ControlUse",
    "Domain",
    "Framework",
    "FrameworkCoverage",
    "RefUse",
    "compliance_rows",
    "compliance_summary",
    "controls_mitigating",
    "framework_refs",
    "has_ai_scope",
    "keep_known_controls",
    "load_catalog",
    "normalize_control_ids",
    "parse_catalog",
    "split_control_ids",
    "spreadsheet_safe",
]
