"""HTML report renderer — single-file, offline view of a STRIDE report.

Output is a self-contained HTML document with inline CSS and no scripts.
Mermaid diagrams are displayed as escaped source rather than executed. Designed as a
human-readable companion to the JSON report — STRIDE category is the primary
visual signal, every threat gets a card, and optional OWASP / Insider lenses
surface as outline pills when present.
"""

from __future__ import annotations

import html
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from stride_gpt.core.controls import (
    Catalog,
    ComplianceSummary,
    compliance_summary,
    load_catalog,
    normalize_control_ids,
)
from stride_gpt.core.report_utils import (
    COMPLIANCE_NOTE,
    SYSTEMIC_OBSERVATIONS_NOTE,
    evidence_items,
    evidence_location,
    join_names,
    mitre_url,
    normalize_mitre_techniques,
    outcome_note,
    related_threat_labels,
)
from stride_gpt.core.schemas import AnalysisReport

# STRIDE category → Tailwind badge classes. Six categories carry distinct
# hues because category is the dominant visual signal, but each pairs a -50
# fill with a matching ring so chips read as categorized tags rather than
# highlighter marks against the slate chrome.
_STRIDE_BADGE_CLASSES: dict[str, str] = {
    "Spoofing": "bg-indigo-50 text-indigo-800 ring-indigo-200",
    "Tampering": "bg-amber-50 text-amber-800 ring-amber-200",
    "Repudiation": "bg-slate-100 text-slate-800 ring-slate-300",
    "Information Disclosure": "bg-rose-50 text-rose-800 ring-rose-200",
    "Denial of Service": "bg-orange-50 text-orange-800 ring-orange-200",
    "Elevation of Privilege": "bg-red-50 text-red-800 ring-red-200",
}
_DEFAULT_BADGE = "bg-slate-50 text-slate-800 ring-slate-200"
_BADGE_BASE = (
    "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium "
    "ring-1 ring-inset"
)
_PILL_BASE = (
    "inline-flex items-center rounded-full ring-1 ring-inset ring-slate-300 "
    "px-2.5 py-0.5 text-xs font-mono text-slate-700"
)
# MITRE pills lean on a subtle sky tint so they're distinguishable from the
# OWASP / Insider pills without competing with the dominant STRIDE badge.
_MITRE_PILL_BASE = (
    "inline-flex items-center rounded-full ring-1 ring-inset ring-sky-300 "
    "bg-sky-50 px-2.5 py-0.5 text-xs font-mono text-sky-800 hover:bg-sky-100"
)
# Control pills get their own emerald tint: they answer "what fixes this",
# a different question from the MITRE / OWASP pills' "what is this".
_CONTROL_PILL_BASE = (
    "inline-flex items-center rounded-full ring-1 ring-inset ring-emerald-300 "
    "bg-emerald-50 px-2.5 py-0.5 text-xs font-mono text-emerald-800"
)
_TABLE = "min-w-full text-sm text-left"
_TH = "px-3 py-2 text-[11px] font-mono uppercase tracking-wider text-slate-500"
_TD = "px-3 py-2 align-top text-slate-800"
# Small uppercase captions inside cards — Scenario, Potential impact, etc.
# Mono ties them to the CLI aesthetic without leaning hard on a "terminal" theme.
_CAPTION = "text-[11px] font-mono uppercase tracking-wider text-slate-500"


def render_html(report: AnalysisReport) -> str:
    """Render an in-memory AnalysisReport as a self-contained HTML document.

    Builds the JSON-shape view inline rather than calling `render_json` from
    `agent.report` — that would create an import cycle (report.py
    lazy-imports this module to write the HTML companion).
    """
    data: dict[str, Any] = {
        "version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "target": report.plan.target_path,
        "overview": report.plan.overall_description,
        "data_flow_diagram": report.data_flow_diagram,
        "subsystems": [
            {
                "name": f.subsystem,
                "threats": f.threats,
                "improvement_suggestions": f.improvement_suggestions,
                "files_analyzed": f.files_analyzed,
                "outcome": f.outcome,
                "error_class": f.error_class,
            }
            for f in report.findings
        ],
        "cross_cutting_threats": report.cross_cutting_threats,
        "systemic_observations": report.systemic_observations,
        "metadata": report.metadata,
    }
    return render_html_from_json(data)


def render_html_from_json(data: dict[str, Any]) -> str:
    """Render a saved JSON report (the disk format) as HTML.

    The two entry points share this implementation so the live `/analyze`
    output and the `/reports` replay path produce byte-identical HTML.
    """
    target = data.get("target") or ""
    target_name = Path(target).name or target or "(unknown target)"
    generated_at = _format_generated_at(data.get("generated_at", ""))
    overview = (data.get("overview") or "").strip()
    dfd_mermaid = (data.get("data_flow_diagram") or "").strip()
    subsystems = data.get("subsystems") or []
    cross_cutting = data.get("cross_cutting_threats") or []
    systemic = data.get("systemic_observations") or []
    metadata = data.get("metadata") or {}

    total_threats = sum(len(s.get("threats") or []) for s in subsystems)
    total_threats += len(cross_cutting)

    parts: list[str] = []
    parts.append(_render_header(
        target_name=target_name,
        generated_at=generated_at,
        metadata=metadata,
        total_threats=total_threats,
        subsystem_count=len(subsystems),
        cross_cutting_count=len(cross_cutting),
        systemic_count=len(systemic),
        synthesis_dropped_count=len(metadata.get("synthesis_dropped") or []),
    ))

    if overview:
        parts.append(_render_overview(overview))

    if dfd_mermaid:
        parts.append(_render_dfd(dfd_mermaid))

    parts.extend(_render_subsystem(sub) for sub in subsystems)

    if cross_cutting:
        parts.append(_render_cross_cutting(cross_cutting))

    if systemic:
        parts.append(_render_systemic_observations(systemic, subsystems))

    all_threats = [t for s in subsystems for t in s.get("threats") or []] + list(cross_cutting)
    summary = compliance_summary(all_threats)
    if summary is not None:
        parts.append(_render_compliance(summary))

    parts.append(_render_footer(metadata))

    body = "\n".join(parts)
    return _scaffold(target_name=target_name, body=body)


# ---------------------------------------------------------------------------
# Scaffold + page chrome
# ---------------------------------------------------------------------------


def _scaffold(*, target_name: str, body: str) -> str:
    title = html.escape(f"STRIDE Threat Model — {target_name}")
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'" />
    <title>{title}</title>
    <style>
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; background: #f8fafc; color: #0f172a; font: 16px/1.55 system-ui, sans-serif; }}
      main {{ max-width: 64rem; margin: auto; padding: 3rem 1.5rem; }}
      main > * + * {{ margin-top: 3rem; }}
      section > * + *, article > * + *, header > * + * {{ margin-top: 1rem; }}
      header {{ border-bottom: 1px solid #e2e8f0; padding-bottom: 1.5rem; }}
      h1, h2, h3, p, dl, dd {{ margin: 0; }}
      h1 {{ font-size: 2rem; line-height: 1.2; }}
      h2 {{ font-size: 1.25rem; }}
      h3 {{ font-size: 1rem; }}
      dt {{ color: #64748b; font-size: .72rem; font-weight: 600; text-transform: uppercase; letter-spacing: .05em; }}
      dl > div + div {{ margin-top: .75rem; }}
      article {{ background: white; border: 1px solid #e2e8f0; border-radius: .5rem; padding: 1.25rem; }}
      article + article {{ margin-top: 1rem; }}
      pre {{ overflow-x: auto; white-space: pre-wrap; overflow-wrap: anywhere; background: #f1f5f9; border-radius: .35rem; padding: .75rem; }}
      code, pre, .font-mono {{ font-family: ui-monospace, monospace; }}
      ul {{ padding-left: 1.5rem; }}
      table {{ width: 100%; border-collapse: collapse; background: white; text-align: left; }}
      th, td {{ border-bottom: 1px solid #e2e8f0; padding: .5rem .75rem; vertical-align: top; }}
      th {{ color: #64748b; font-size: .7rem; text-transform: uppercase; }}
      a {{ color: #075985; }}
      .overflow-x-auto, .overflow-auto {{ overflow-x: auto; }}
      .inline-flex {{ display: inline-flex; align-items: center; margin: .1rem; border: 1px solid #cbd5e1; border-radius: 999px; padding: .15rem .65rem; font-size: .75rem; }}
      .bg-indigo-50 {{ background: #eef2ff; color: #3730a3; }}
      .bg-amber-50, .bg-amber-50\\/60 {{ background: #fffbeb; color: #92400e; }}
      .bg-rose-50 {{ background: #fff1f2; color: #9f1239; }}
      .bg-orange-50 {{ background: #fff7ed; color: #9a3412; }}
      .bg-red-50 {{ background: #fef2f2; color: #991b1b; }}
      .bg-sky-50 {{ background: #f0f9ff; color: #075985; }}
      .bg-emerald-50 {{ background: #ecfdf5; color: #065f46; }}
      .text-xs {{ font-size: .75rem; }}
      .text-sm {{ font-size: .875rem; }}
      .italic {{ font-style: italic; }}
      footer {{ border-top: 1px solid #e2e8f0; padding-top: 1.5rem; color: #64748b; }}
      @media print {{ body {{ background: white; }} main {{ padding: 0; }} article {{ break-inside: avoid; }} }}
    </style>
  </head>
  <body class="bg-slate-50 text-slate-900 font-sans">
    <main class="max-w-5xl mx-auto px-6 py-12 space-y-12">
{body}
    </main>
  </body>
</html>
"""


def _render_header(
    *,
    target_name: str,
    generated_at: str,
    metadata: dict[str, Any],
    total_threats: int,
    subsystem_count: int,
    cross_cutting_count: int,
    systemic_count: int = 0,
    synthesis_dropped_count: int = 0,
) -> str:
    model_line = _format_model_line(metadata)
    chip = (
        "inline-flex items-center rounded-full bg-white ring-1 ring-inset ring-slate-200 "
        "px-3 py-1 text-xs font-mono text-slate-700"
    )

    summary_chips = [
        f'<span class="{chip}">{total_threats} threats</span>',
    ]
    # /quick reports collapse to one synthetic "Application" subsystem; showing
    # "1 subsystem" there would be misleading, so suppress when ≤1.
    if subsystem_count > 1:
        summary_chips.append(f'<span class="{chip}">{subsystem_count} subsystems</span>')
    if cross_cutting_count:
        summary_chips.append(
            f'<span class="{chip}">{cross_cutting_count} cross-cutting</span>'
        )
    if systemic_count:
        summary_chips.append(
            f'<span class="{chip}">{systemic_count} systemic observations</span>'
        )
    synthesis_error_class = metadata.get("synthesis_error_class")
    if isinstance(synthesis_error_class, str) and synthesis_error_class:
        summary_chips.append(
            f'<span class="{chip}">Synthesis failed ({html.escape(synthesis_error_class)})</span>'
        )
    # Otherwise a run whose every synthesis item was dropped reads the same as
    # one where synthesis genuinely found nothing.
    if synthesis_dropped_count:
        summary_chips.append(
            f'<span class="{chip}">{synthesis_dropped_count} synthesis items dropped</span>'
        )

    meta_line_parts: list[str] = []
    if generated_at:
        meta_line_parts.append(f"Generated {html.escape(generated_at)}")
    if model_line:
        meta_line_parts.append(html.escape(model_line))
    meta_line = " · ".join(meta_line_parts)

    return f"""      <header class="border-b border-slate-200 pb-8 space-y-4">
        <p class="font-mono text-xs tracking-tight text-slate-500">
          <span class="text-slate-400">&rsaquo;</span>
          <span class="text-slate-700">stride-gpt</span>
          <span class="text-slate-400">threat-model</span>
        </p>
        <h1 class="text-3xl font-semibold tracking-tight text-slate-900">{html.escape(target_name)}</h1>
        <p class="text-sm text-slate-600">{meta_line}</p>
        <div class="flex flex-wrap gap-2 pt-2">{"".join(summary_chips)}</div>
      </header>"""


def _render_overview(overview: str) -> str:
    return f"""      <section id="overview" class="space-y-3">
        <h2 class="{_CAPTION}">Overview</h2>
        <p class="text-base leading-relaxed text-slate-800">{html.escape(overview)}</p>
      </section>"""


def _render_dfd(dfd_mermaid: str) -> str:
    """Show model-generated Mermaid as escaped source without executing it."""
    return f"""      <section id="data-flow-diagram" class="space-y-3">
        <h2 class="{_CAPTION}">Data Flow Diagram</h2>
        <p class="text-sm">Mermaid source (render separately in a trusted offline viewer).</p>
        <div class="rounded-lg bg-white ring-1 ring-slate-200 p-4 overflow-auto">
          <pre class="mermaid">{html.escape(dfd_mermaid)}</pre>
        </div>
      </section>"""


def _render_footer(metadata: dict[str, Any]) -> str:
    bits: list[str] = []
    llm_calls = metadata.get("llm_calls")
    tool_calls = metadata.get("tool_calls")
    if llm_calls is not None:
        bits.append(f"{llm_calls} LLM calls")
    if tool_calls is not None:
        bits.append(f"{tool_calls} tool calls")
    model_line = _format_model_line(metadata)
    if model_line:
        bits.append(model_line)
    line = " · ".join(bits)
    return f"""      <footer class="border-t border-slate-200 pt-6 font-mono text-xs text-slate-500">
        <span class="text-slate-400">&rsaquo;</span> generated by stride-gpt{(" · " + html.escape(line)) if line else ""}
      </footer>"""


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------


# A subsystem that didn't finish is a caveat about the report, not a threat
# category — so it reads as a bordered callout rather than another round chip.
# Every Tailwind hue is already spoken for by the six STRIDE badges, and a
# seventh pill would compete with the one signal the page is built around.
_OUTCOME_CALLOUT = (
    "rounded-r border-l-4 border-amber-400 bg-amber-50/60 px-3 py-2 text-sm "
    "text-amber-900"
)


def _render_outcome_callout(outcome: str, error_class: str | None) -> str:
    """Why a subsystem didn't complete, or "" when it did.

    Reports that show only threats make a crashed subsystem indistinguishable
    from a clean one, which is the whole point of recording the outcome.
    """
    note = outcome_note(outcome, error_class)
    if note is None:
        return ""
    label = outcome.replace("_", " ")
    return (
        f'        <p class="{_OUTCOME_CALLOUT}">'
        f"<span class=\"font-medium\">{html.escape(label)}</span> — "
        f"{html.escape(note)}.</p>"
    )


def _render_subsystem(sub: dict[str, Any]) -> str:
    name = sub.get("name") or "(unnamed)"
    description = (sub.get("description") or "").strip()
    files = sub.get("files_analyzed") or []
    threats = sub.get("threats") or []
    suggestions = sub.get("improvement_suggestions") or []
    # Reports saved before outcomes existed have no key; anything written out
    # at all had been analysed.
    outcome = sub.get("outcome") or "completed"
    callout = _render_outcome_callout(outcome, sub.get("error_class"))

    parts: list[str] = []
    parts.append(f"""        <header class="space-y-1">
          <h2 class="text-xl font-semibold tracking-tight text-slate-900">{html.escape(name)}</h2>""")
    if description:
        parts.append(
            f'          <p class="text-sm text-slate-600">{html.escape(description)}</p>'
        )
    parts.append("        </header>")

    if callout:
        parts.append(callout)

    if files:
        parts.append(_render_files_analyzed(files))

    if threats:
        cards = "\n".join(_render_threat_card(t, cross_cutting=False) for t in threats)
        parts.append(f"""        <div class="space-y-4">
{cards}
        </div>""")
    elif outcome == "completed":
        parts.append(
            '        <p class="text-sm italic text-slate-500">No threats identified.</p>'
        )

    if suggestions:
        parts.append(_render_recommendations(suggestions))

    body = "\n".join(parts)
    return f"""      <section class="space-y-5">
{body}
      </section>"""


def _render_cross_cutting(threats: list[dict[str, Any]]) -> str:
    cards = "\n".join(_render_threat_card(t, cross_cutting=True) for t in threats)
    return f"""      <section id="cross-cutting" class="space-y-5">
        <header class="space-y-1">
          <h2 class="text-xl font-semibold tracking-tight text-slate-900">Cross-cutting threats</h2>
          <p class="text-sm text-slate-600">Issues that span multiple subsystems.</p>
        </header>
        <div class="space-y-4">
{cards}
        </div>
      </section>"""


def _render_systemic_observations(
    observations: list[dict[str, Any]], subsystems: list[dict[str, Any]]
) -> str:
    pairs = [(sub.get("name") or "", sub.get("threats") or []) for sub in subsystems]
    cards = "\n".join(_render_observation_card(o, pairs) for o in observations)
    return f"""      <section id="systemic-observations" class="space-y-5">
        <header class="space-y-1">
          <h2 class="text-xl font-semibold tracking-tight text-slate-900">Systemic observations</h2>
          <p class="text-sm text-slate-600">{html.escape(SYSTEMIC_OBSERVATIONS_NOTE)}</p>
        </header>
        <div class="space-y-4">
{cards}
        </div>
      </section>"""


def _render_observation_card(
    observation: dict[str, Any], subsystems: list[tuple[str, list[dict[str, Any]]]]
) -> str:
    threat_type = observation.get("Threat Type") or "Unknown"
    badge_classes = _STRIDE_BADGE_CLASSES.get(threat_type, _DEFAULT_BADGE)
    rows: list[str] = []
    if observation.get("Scenario"):
        rows.append(_dl_row("Observation", html.escape(str(observation["Scenario"]))))
    if observation.get("Potential Impact"):
        rows.append(_dl_row("Potential impact", html.escape(str(observation["Potential Impact"]))))
    affected = observation.get("Affected Subsystems") or []
    if affected:
        pills = "".join(
            f'<span class="{_PILL_BASE}">{html.escape(str(a))}</span> ' for a in affected
        )
        rows.append(_dl_row("Affects", f'<div class="flex flex-wrap gap-1">{pills}</div>'))
    links = related_threat_labels(observation, subsystems)
    if links:
        items = "".join(
            f'<li><span class="font-mono text-xs">{html.escape(tid)}</span>'
            + (f" &mdash; {html.escape(label)}" if label else "")
            + "</li>"
            for tid, label in links
        )
        rows.append(_dl_row("Summarises", f'<ul class="list-disc pl-5 space-y-1">{items}</ul>'))
    body = "\n".join(rows)
    return f"""          <article class="rounded-lg border border-dashed border-slate-300 bg-white p-5 space-y-3">
            <div class="flex flex-wrap gap-2"><span class="{_BADGE_BASE} {badge_classes}">{html.escape(str(threat_type))}</span></div>
            <dl class="space-y-3">
{body}
            </dl>
          </article>"""


def _render_files_analyzed(files: list[str]) -> str:
    items = "\n".join(
        f'            <li class="font-mono text-xs text-slate-700">{html.escape(f)}</li>'
        for f in files
    )
    return f"""        <div>
          <h3 class="{_CAPTION} mb-2">Files analyzed</h3>
          <ul class="space-y-1">
{items}
          </ul>
        </div>"""


def _render_recommendations(suggestions: list[str]) -> str:
    items = "\n".join(
        f'            <li>{html.escape(str(s))}</li>' for s in suggestions
    )
    return f"""        <div class="rounded-lg border border-slate-200 bg-white p-5">
          <h3 class="{_CAPTION} mb-3">Recommendations</h3>
          <ul class="list-disc pl-5 space-y-1 text-sm text-slate-800">
{items}
          </ul>
        </div>"""


# ---------------------------------------------------------------------------
# Threat card
# ---------------------------------------------------------------------------


def _render_threat_card(threat: dict[str, Any], *, cross_cutting: bool) -> str:
    threat_type = threat.get("Threat Type") or "Unknown"
    scenario = str(threat.get("Scenario") or "")
    impact = str(threat.get("Potential Impact") or "")
    owasp_llm = threat.get("OWASP_LLM")
    owasp_asi = threat.get("OWASP_ASI")
    insider = threat.get("INSIDER_CATEGORY")
    mitre = threat.get("MITRE_ATTACK")
    affected = threat.get("Affected Subsystems") or []

    badge_classes = _STRIDE_BADGE_CLASSES.get(threat_type, _DEFAULT_BADGE)

    badges: list[str] = [
        f'<span class="{_BADGE_BASE} {badge_classes}">{html.escape(str(threat_type))}</span>'
    ]
    if owasp_llm:
        badges.append(f'<span class="{_PILL_BASE}">OWASP {html.escape(str(owasp_llm))}</span>')
    if owasp_asi:
        badges.append(f'<span class="{_PILL_BASE}">ASI {html.escape(str(owasp_asi))}</span>')
    if insider:
        badges.append(
            f'<span class="{_PILL_BASE}">Insider: {html.escape(str(insider))}</span>'
        )
    badges.extend(_render_mitre_pills(mitre))
    badges.extend(_render_control_pills(threat.get("CONTROLS")))

    rows: list[str] = []
    if scenario:
        rows.append(_dl_row("Scenario", html.escape(scenario)))
    if impact:
        rows.append(_dl_row("Potential impact", html.escape(impact)))
    if evidence_items(threat):
        rows.append(_dl_row("Evidence", _render_evidence(threat)))
    if cross_cutting and affected:
        pills = "".join(
            f'<span class="{_PILL_BASE}">{html.escape(str(a))}</span> '
            for a in affected
        )
        rows.append(_dl_row("Affects", f'<div class="flex flex-wrap gap-1">{pills}</div>'))

    badge_row = "".join(b + " " for b in badges)
    body = "\n".join(rows)
    return f"""          <article class="rounded-lg border border-slate-200 bg-white p-5 space-y-3">
            <div class="flex flex-wrap gap-2">{badge_row}</div>
            <dl class="space-y-3">
{body}
            </dl>
          </article>"""


def _render_mitre_pills(value: Any) -> list[str]:
    """Render MITRE ATT&CK techniques as linked pills.

    Delegates shape handling to
    :func:`stride_gpt.core.report_utils.normalize_mitre_techniques`, so the
    canonical list-of-objects, the list-of-strings fallback, and the comma-
    separated-string shape all render. Each pill links to attack.mitre.org /
    atlas.mitre.org when the ID matches a known prefix; otherwise it renders
    as plain text. Returns an empty list if the field is absent / empty /
    malformed — threat cards without MITRE mappings render exactly as before.
    """
    techniques = normalize_mitre_techniques(value)
    if not techniques:
        return []
    pills: list[str] = []
    for tid, name in techniques:
        label = f"{tid} {name}" if name else tid
        url = mitre_url(tid)
        if url:
            pills.append(
                f'<a class="{_MITRE_PILL_BASE}" href="{html.escape(url)}" '
                f'target="_blank" rel="noopener noreferrer" title="{html.escape(label)}">'
                f'{html.escape(tid)}</a>'
            )
        else:
            pills.append(
                f'<span class="{_MITRE_PILL_BASE}" title="{html.escape(label)}">'
                f'{html.escape(tid)}</span>'
            )
    return pills


def _render_control_pills(value: Any) -> list[str]:
    """Catalogue controls as pills, the control's name in the tooltip.

    Only IDs the catalogue knows render, through the same normaliser the
    markdown and SARIF renderers use. Not links: the report is a standalone
    file and the catalogue docs may not live where a link would point.
    """
    catalog = load_catalog()
    pills: list[str] = []
    for cid in normalize_control_ids(value):
        control = catalog.control(cid)
        title = f"{cid} {control.name}" if control else cid
        pills.append(
            f'<span class="{_CONTROL_PILL_BASE}" title="{html.escape(title)}">'
            f"{html.escape(cid)}</span>"
        )
    return pills


def _render_compliance(summary: ComplianceSummary) -> str:
    """Recommended controls and the framework references they bear on.

    Every value here comes from the packaged catalogue, keyed by IDs the
    renderer has already validated; it's escaped anyway, like everything else
    on the page.
    """
    catalog = load_catalog()
    control_rows = "\n".join(
        f"""              <tr class="border-t border-slate-100">
                <td class="{_TD}"><span class="{_CONTROL_PILL_BASE}">{html.escape(use.control.id)}</span></td>
                <td class="{_TD}">{html.escape(use.control.name)}</td>
                <td class="{_TD} text-slate-600">{html.escape(_domain_title(catalog, use.control.domain))}</td>
                <td class="{_TD} font-mono">{use.threat_count}</td>
              </tr>"""
        for use in summary.controls
    )
    tables = [
        _compliance_table(
            "Recommended controls",
            ("Control", "Name", "Domain", "Threats"),
            control_rows,
        )
    ]
    for coverage in summary.frameworks:
        framework = coverage.framework
        if not coverage.refs:
            tables.append(
                f"""        <div class="space-y-2">
          <h3 class="text-base font-semibold text-slate-900">{html.escape(framework.name)}</h3>
          <p class="text-sm italic text-slate-500">No {html.escape(framework.name)} references for the recommended controls.</p>
        </div>"""
            )
            continue
        rows = "\n".join(
            f"""              <tr class="border-t border-slate-100">
                <td class="{_TD} font-mono whitespace-nowrap">{html.escape(ref.ref)}</td>
                <td class="{_TD}">{html.escape(ref.title)}</td>
                <td class="{_TD}"><div class="flex flex-wrap gap-1">{"".join(f'<span class="{_CONTROL_PILL_BASE}">{html.escape(cid)}</span>' for cid in ref.control_ids)}</div></td>
                <td class="{_TD} font-mono">{ref.threat_count}</td>
              </tr>"""
            for ref in coverage.refs
        )
        tables.append(
            _compliance_table(
                framework.name,
                ("Reference", "Requirement", "Controls", "Threats"),
                rows,
                subtitle=framework.full_name,
            )
        )
    omitted = summary.omitted_frameworks
    if omitted:
        names = join_names(f.name for f in omitted)
        tables.append(
            f'        <p class="text-sm italic text-slate-500">{html.escape(names)} references '
            "are omitted because no threat in this report concerns an AI system.</p>"
        )
    body = "\n".join(tables)
    return f"""      <section id="controls-compliance" class="space-y-5">
        <header class="space-y-1">
          <h2 class="text-xl font-semibold tracking-tight text-slate-900">Controls &amp; compliance</h2>
          <p class="text-sm text-slate-600">{html.escape(COMPLIANCE_NOTE)} Catalogue version {html.escape(summary.catalog_version)}.</p>
        </header>
{body}
      </section>"""


def _compliance_table(
    title: str, headers: tuple[str, ...], rows: str, *, subtitle: str = ""
) -> str:
    head = "".join(f'<th class="{_TH}">{html.escape(h)}</th>' for h in headers)
    sub = (
        f'\n          <p class="text-xs text-slate-500">{html.escape(subtitle)}</p>'
        if subtitle
        else ""
    )
    return f"""        <div class="space-y-2">
          <h3 class="text-base font-semibold text-slate-900">{html.escape(title)}</h3>{sub}
          <div class="overflow-x-auto rounded-lg border border-slate-200 bg-white">
            <table class="{_TABLE}">
              <thead><tr>{head}</tr></thead>
              <tbody>
{rows}
              </tbody>
            </table>
          </div>
        </div>"""


def _domain_title(catalog: Catalog, key: str) -> str:
    domain = catalog.domain(key)
    return domain.title if domain else key


def _render_evidence(threat: dict[str, Any]) -> str:
    """The code a threat cites, with the line range the snippet matched.

    An unverified item is shown, not hidden: the snippet is still what the
    model based the threat on, and saying we couldn't find it is more useful
    than dropping it silently.
    """
    rows: list[str] = []
    for item in evidence_items(threat):
        location = html.escape(evidence_location(item))
        snippet = html.escape(str(item.get("snippet") or ""))
        occurrences = item.get("occurrences")
        if not item.get("verified"):
            flag = f' <span class="{_PILL_BASE}">unverified</span>'
        elif isinstance(occurrences, int) and occurrences > 1:
            # The range is the first match; say so rather than imply it is
            # the only one.
            flag = f' <span class="{_PILL_BASE}">{occurrences} matches</span>'
        else:
            flag = ""
        rows.append(
            f"""                <li>
                  <div class="font-mono text-xs text-slate-600">{location}{flag}</div>
                  <pre class="mt-1 overflow-x-auto rounded bg-slate-50 p-2 text-xs \
font-mono text-slate-800"><code>{snippet}</code></pre>
                </li>"""
        )
    return f"""<ul class="space-y-2">
{chr(10).join(rows)}
              </ul>"""


def _dl_row(label: str, value_html: str) -> str:
    return f"""              <div>
                <dt class="{_CAPTION}">{label}</dt>
                <dd class="text-sm leading-relaxed text-slate-800">{value_html}</dd>
              </div>"""


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _format_generated_at(raw: str) -> str:
    """Convert ISO-8601 to a humane 'YYYY-MM-DD HH:MM UTC' form.

    Falls back to the raw string if parsing fails — we never want a report
    timestamp to break the renderer.
    """
    if not raw:
        return ""
    try:
        cleaned = raw.rstrip("Z")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, TypeError):
        return raw


def _format_model_line(metadata: dict[str, Any]) -> str:
    worker = metadata.get("worker_model")
    worker_provider = metadata.get("worker_provider", "")
    architect = metadata.get("architect_model")
    architect_provider = metadata.get("architect_provider", "")
    if architect:
        return (
            f"Architect: {architect_provider}/{architect} · "
            f"Worker: {worker_provider}/{worker}"
        )
    if worker:
        return f"Model: {worker_provider}/{worker}"
    return ""
