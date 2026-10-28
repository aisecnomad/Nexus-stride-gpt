"""Render the control catalogue into reference cards and documentation.

Generated, not hand-written, for the same reason the MITRE cards are: the
model must only see IDs that exist, and the docs must say exactly what the
mappings say. ``scripts/build_control_catalog.py`` writes every file in
:func:`generated_files`; ``tests/test_controls.py`` fails if a committed copy
has drifted from the catalogue.
"""

from __future__ import annotations

import textwrap

from stride_gpt.core.controls import (
    STRIDE_LETTERS,
    STRIDE_NAMES,
    Control,
    load_catalog,
)

CARD_DIR = "stride_gpt/core/prompts/threat_model"
CATALOG_DOC = "docs/controls-catalog.md"
CROSSWALK_DOC = "docs/framework-crosswalks.md"
_DOCS_URL = "https://github.com/mrwadams/stride-gpt/blob/master/docs/controls-catalog.md"

_GENERATED_NOTE = (
    "Generated from stride_gpt/core/controls/catalog.toml by "
    "scripts/build_control_catalog.py. Edit the catalogue, not this file."
)

# OWASP lists the crosswalk groups codes under, in display order.
_OWASP_LISTS = (
    ("OWASP Top 10:2025", ":2025"),
    ("OWASP Top 10 for LLM Applications (2025)", "LLM"),
    ("OWASP Top 10 for Agentic Applications (2026)", "ASI"),
)


def generated_files() -> dict[str, str]:
    """Every generated file, keyed by its path relative to the repo root."""
    catalog = load_catalog()
    files = {f"{CARD_DIR}/{card.name}.md": render_card(card.name) for card in catalog.cards}
    files[CATALOG_DOC] = render_catalog_doc()
    files[CROSSWALK_DOC] = render_crosswalks_doc()
    return files


# ---------------------------------------------------------------------------
# Reference cards
# ---------------------------------------------------------------------------


def render_card(name: str) -> str:
    """A progressive-disclosure reference card for one group of domains."""
    catalog = load_catalog()
    card = catalog.card(name)
    if card is None:
        raise KeyError(f"no card named {name!r} in the control catalogue")

    when = textwrap.wrap(card.when_to_load, width=74)
    example = ", ".join(f'"{cid}"' for cid in card.example)
    other_cards = [c.name for c in catalog.cards if c.name != name]

    lines = [
        "---",
        *(f"# {line}" for line in textwrap.wrap(_GENERATED_NOTE, width=76)),
        f"name: {card.name}",
        f"title: {card.title}",
        "when_to_load: |",
        *(f"  {line}" for line in when),
        "adds_fields:",
        "  - CONTROLS",
        f"stride_letters: [{', '.join(STRIDE_LETTERS)}]",
        f"source: {_DOCS_URL}",
        f"version: {catalog.version}",
        "---",
        "",
        f"# {card.title} — Reference Card",
        "",
        card.intro,
        "",
        "## How to use this card",
        "",
        "- For each threat, choose **1-4** control IDs that would most directly prevent, "
        "detect or contain it, most important first.",
        "- Prefer the most specific control. A threat about a *missing* control cites that "
        "control.",
        "- **Anti-hallucination requirement.** Use only IDs listed in the control cards you "
        "loaded, exactly as written. Never invent an ID; if nothing fits, leave the field "
        "out rather than guess.",
        "- Do not cite framework clauses yourself. STRIDE-GPT looks up the AIUC-1, "
        "ISO/IEC 42001, ISO/IEC 27001 and EU AI Act references for the IDs you choose.",
    ]
    if other_cards:
        lines.append(
            "- IDs from "
            + " and ".join(f"`{other}`" for other in other_cards)
            + " are equally valid; a threat can combine IDs from both cards."
        )
    lines += [
        "",
        "## Schema additions",
        "",
        "Each threat must additionally include:",
        f'- `"CONTROLS"`: an array of control IDs, e.g. `[{example}]`. When reporting '
        "through `report_threat`, pass them as the `controls` argument.",
        "",
        "## Control catalogue",
    ]
    for domain in catalog.domains:
        if domain.card != name:
            continue
        lines += ["", f"### {domain.key} — {domain.title}", ""]
        lines.extend(
            f"- `{c.id}` **{c.name}.** {c.objective}" + _stride_suffix(c)
            for c in catalog.controls
            if c.domain == domain.key
        )
    lines.append("")
    return "\n".join(lines)


def _stride_suffix(control: Control) -> str:
    return f" ({', '.join(control.stride)})" if control.stride else ""


# ---------------------------------------------------------------------------
# docs/controls-catalog.md
# ---------------------------------------------------------------------------


def render_catalog_doc() -> str:
    """The full catalogue: every control with guidance, mappings and sources."""
    catalog = load_catalog()
    names = ", ".join(f.name for f in catalog.frameworks)
    lines = [
        f"<!-- {_GENERATED_NOTE} -->",
        "",
        "# Control Catalogue",
        "",
        f"Catalogue version **{catalog.version}** · {len(catalog.controls)} controls in "
        f"{len(catalog.domains)} domains · mapped to {names}.",
        "",
        "STRIDE-GPT tags each threat with the IDs of the controls that would mitigate it, "
        "and looks up the framework references below from those IDs. See "
        "[Controls and compliance mapping](controls-and-compliance.md) for how the mapping "
        "works and its limits, and [Framework crosswalks](framework-crosswalks.md) for the "
        "same data organised by framework.",
        "",
        "## Domains",
        "",
        "| Domain | Controls | Reference card | Scope |",
        "|--------|----------|----------------|-------|",
    ]
    for domain in catalog.domains:
        count = sum(1 for c in catalog.controls if c.domain == domain.key)
        lines.append(
            f"| [{domain.key} — {domain.title}](#domain-{domain.key.lower()}) | {count} | "
            f"`{domain.card}` | {_cell(domain.summary)} |"
        )

    for domain in catalog.domains:
        lines += [
            "",
            f'<a id="domain-{domain.key.lower()}"></a>',
            "",
            f"## {domain.key} — {domain.title}",
            "",
            domain.summary,
            "",
            "| ID | Control | STRIDE |",
            "|----|---------|--------|",
        ]
        controls = [c for c in catalog.controls if c.domain == domain.key]
        lines.extend(
            f"| [{c.id}](#{c.id.lower()}) | {_cell(c.name)} | {', '.join(c.stride) or '—'} |"
            for c in controls
        )
        for control in controls:
            lines += ["", f'<a id="{control.id.lower()}"></a>', *control_markdown_lines(control)]
    lines.append("")
    return "\n".join(lines)


def control_markdown_lines(control: Control) -> list[str]:
    """One control in full: objective, guidance, mappings and sources.

    Shared by the catalogue doc and ``stride-gpt controls <ID>``.
    """
    catalog = load_catalog()
    lines = [
        "",
        f"### {control.id} · {control.name}",
        "",
        f"**Objective.** {control.objective}",
        "",
        "**Guidance**",
        "",
        *(f"- {item}" for item in control.guidance),
        "",
        "| | |",
        "|---|---|",
        "| STRIDE | "
        + (", ".join(STRIDE_NAMES[s] for s in control.stride) or "—")
        + " |",
    ]
    if control.mitigates:
        lines.append(
            "| Mitigates | "
            + "; ".join(f"{code} {catalog.owasp_title(code)}" for code in control.mitigates)
            + " |"
        )
    for framework in catalog.frameworks:
        refs = control.refs_for(framework.key)
        rendered = "<br>".join(f"{ref} — {_cell(framework.title(ref))}" for ref in refs)
        lines.append(f"| {framework.name} | {rendered or '—'} |")
    if control.references:
        lines.append(f"| Sources | {_cell('; '.join(control.references))} |")
    return lines


# ---------------------------------------------------------------------------
# docs/framework-crosswalks.md
# ---------------------------------------------------------------------------


def render_crosswalks_doc() -> str:
    """The catalogue organised by framework, OWASP risk and STRIDE category."""
    catalog = load_catalog()
    lines = [
        f"<!-- {_GENERATED_NOTE} -->",
        "",
        "# Framework Crosswalks",
        "",
        f"Catalogue version **{catalog.version}**. For each framework: every reference the "
        "control catalogue maps to, the controls that address it, and the references no "
        "control addresses. A reference with no control is usually an organisational "
        "process outside the reach of a threat model, not an oversight; see "
        "[Controls and compliance mapping](controls-and-compliance.md#what-the-mapping-is-and-isnt).",
        "",
        "Contents: "
        + " · ".join(f"[{f.name}](#{f.key.replace('_', '-')})" for f in catalog.frameworks)
        + " · [OWASP](#owasp) · [STRIDE](#stride)",
    ]

    for framework in catalog.frameworks:
        by_ref: dict[str, list[str]] = {}
        for control in catalog.controls:
            for ref in control.refs_for(framework.key):
                by_ref.setdefault(ref, []).append(control.id)
        lines += [
            "",
            f'<a id="{framework.key.replace("_", "-")}"></a>',
            "",
            f"## {framework.name}",
            "",
            f"[{framework.full_name}]({framework.url}) · version: {framework.version}",
            "",
            f"> {framework.note}",
            "",
            "| Reference | Requirement | Controls |",
            "|-----------|-------------|----------|",
        ]
        lines.extend(
            f"| {ref} | {_cell(title)} | {_control_links(by_ref[ref])} |"
            for ref, title in framework.refs
            if ref in by_ref
        )
        unmapped = [(ref, title) for ref, title in framework.refs if ref not in by_ref]
        covered = len(framework.refs) - len(unmapped)
        lines += [
            "",
            f"**Coverage:** {covered} of {len(framework.refs)} listed references are "
            "addressed by at least one catalogue control.",
        ]
        if unmapped:
            lines += ["", "Not addressed by a catalogue control:", ""]
            lines.extend(f"- {ref} — {title}" for ref, title in unmapped)

    lines += ['', '<a id="owasp"></a>', "", "## OWASP"]
    for heading, marker in _OWASP_LISTS:
        codes = [(code, title) for code, title in catalog.owasp if marker in code]
        lines += [
            "",
            f"### {heading}",
            "",
            "| Code | Risk | Controls |",
            "|------|------|----------|",
        ]
        lines.extend(
            f"| {code} | {_cell(title)} | "
            f"{_control_links([c.id for c in catalog.controls if code in c.mitigates]) or '—'} |"
            for code, title in codes
        )

    lines += [
        "",
        '<a id="stride"></a>',
        "",
        "## STRIDE",
        "",
        "| Category | Controls |",
        "|----------|----------|",
    ]
    lines.extend(
        f"| {STRIDE_NAMES[letter]} | "
        f"{_control_links([c.id for c in catalog.controls if letter in c.stride])} |"
        for letter in STRIDE_LETTERS
    )
    lines.append("")
    return "\n".join(lines)


def _control_links(ids: list[str]) -> str:
    return ", ".join(f"[{cid}](controls-catalog.md#{cid.lower()})" for cid in ids)


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")
