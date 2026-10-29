"""Tests for the control catalogue, its deterministic framework mapping, and
how CONTROLS flows through the agent, the renderers, the CLI and the web UI.

The contract under test: the model only ever chooses control IDs; every
framework reference in a report is a lookup in the packaged catalogue. So the
tests check the catalogue's integrity (every mapping resolves), that invented
IDs never survive into a report, and that every surface agrees on the
reading of a threat's CONTROLS.
"""

from __future__ import annotations

import copy
import csv
import io
import json
import tomllib
from importlib.resources import files
from pathlib import Path

import pytest
from typer.testing import CliRunner

from stride_gpt import cli
from stride_gpt.agent.html_report import render_html, render_html_from_json
from stride_gpt.agent.loop import _apply_control_ids, classify_synthesis
from stride_gpt.agent.quick import _parse_threat_model, run_quick_analysis
from stride_gpt.agent.report import (
    render_json,
    render_markdown,
    render_markdown_from_json,
    render_sarif,
    save_quick_report,
)
from stride_gpt.agent.tools import REPORTING_TOOLS, THREAT_ARG_TO_FIELD
from stride_gpt.core.controls import (
    AI_DOMAINS,
    COMPLIANCE_ROW_FIELDS,
    CatalogError,
    compliance_rows,
    compliance_summary,
    controls_mitigating,
    framework_refs,
    has_ai_scope,
    keep_known_controls,
    load_catalog,
    normalize_control_ids,
    parse_catalog,
    split_control_ids,
    spreadsheet_safe,
)
from stride_gpt.core.controls.render import generated_files
from stride_gpt.core.prompts import create_threat_model_prompt
from stride_gpt.core.prompts.variants import list_references, load_reference
from stride_gpt.core.report_utils import (
    compliance_section_lines,
    detect_extra_columns,
    threat_table_header,
    threat_table_row,
)
from stride_gpt.core.schemas import AnalysisReport, SubsystemFinding, ToolCallResult
from stride_gpt.core.threat_model import json_to_markdown
from tests.fakes import QUICK_TOOL_NAMES, ScriptedLLM, call_tools, reply

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_FRAMEWORKS = {"aiuc_1", "iso_42001", "eu_ai_act"}

# A non-AI threat (plain web app) and an agentic one, each carrying controls.
WEB_THREAT = {
    "Threat Type": "Spoofing",
    "Scenario": "JWTs are accepted with alg=none.",
    "Potential Impact": "Account takeover.",
    "CONTROLS": ["IAM-05", "LOG-01"],
}
AGENT_THREAT = {
    "Threat Type": "Elevation of Privilege",
    "Scenario": "The agent can call the refund tool with any amount.",
    "Potential Impact": "Financial loss.",
    "OWASP_ASI": "ASI02",
    "CONTROLS": ["AGT-05", "AGT-07", "IAM-05"],
}


def _raw_catalog() -> dict:
    text = (files("stride_gpt.core.controls") / "catalog.toml").read_text(encoding="utf-8")
    return tomllib.loads(text)


# ---------------------------------------------------------------------------
# Catalogue integrity
# ---------------------------------------------------------------------------


class TestCatalogIntegrity:
    def test_loads_and_validates(self):
        catalog = load_catalog()
        assert catalog.version
        assert len(catalog.controls) >= 60

    def test_ids_are_unique_and_prefixed_by_domain(self):
        catalog = load_catalog()
        ids = catalog.control_ids
        assert len(ids) == len(set(ids))
        for control in catalog.controls:
            assert control.id.startswith(control.domain + "-")

    def test_every_domain_has_controls_and_a_card(self):
        catalog = load_catalog()
        card_names = {c.name for c in catalog.cards}
        for domain in catalog.domains:
            assert domain.card in card_names
            assert any(c.domain == domain.key for c in catalog.controls), domain.key

    def test_maps_to_the_four_frameworks(self):
        catalog = load_catalog()
        assert {f.key for f in catalog.frameworks} == AI_FRAMEWORKS | {"iso_27001"}
        for framework in catalog.frameworks:
            assert framework.ai_specific is (framework.key in AI_FRAMEWORKS)

    def test_iso_42001_registry_lists_all_38_annex_a_controls(self):
        """A dropped Annex A control would silently vanish from the coverage
        report, so the registry's completeness is pinned."""
        iso = load_catalog().framework("iso_42001")
        assert iso is not None
        annex_a = [ref for ref, _ in iso.refs if ref.startswith("A.")]
        assert len(annex_a) == 38

    def test_every_framework_has_at_least_one_mapped_control(self):
        catalog = load_catalog()
        for framework in catalog.frameworks:
            assert any(c.refs_for(framework.key) for c in catalog.controls), framework.key

    def test_requested_control_areas_are_covered(self):
        """IAM (X.509, JWT, OAuth), data protection (CMEK, TLS, mTLS), network
        (MACsec, IPsec), logging and OWASP application security each have a
        control a threat can cite."""
        text = {
            c.id: f"{c.name} {c.objective} {' '.join(c.guidance)}"
            for c in load_catalog().controls
        }
        for needle in ("X.509", "JWT", "OAuth", "CMEK", "TLS 1.3", "Mutual TLS",
                       "MACsec", "IPsec", "OWASP", "kill switch"):
            assert any(needle.lower() in t.lower() for t in text.values()), needle

    def test_every_owasp_risk_has_a_mitigating_control(self):
        """Every OWASP Top 10:2025, LLM Top 10 and Agentic Top 10 risk the
        catalogue lists is addressed by at least one control."""
        catalog = load_catalog()
        for code, _title in catalog.owasp:
            assert controls_mitigating(code), code

    def test_every_stride_category_is_covered(self):
        catalog = load_catalog()
        for letter in "STRIDE":
            assert any(letter in c.stride for c in catalog.controls), letter

    def test_objectives_stay_short_for_the_card_budget(self):
        """Objectives are what the model reads on every analysis; guidance is
        for the docs."""
        for control in load_catalog().controls:
            assert len(control.objective) <= 320, control.id


class TestCatalogValidation:
    """parse_catalog must refuse a catalogue whose references don't resolve —
    that's what keeps an invented clause out of every report."""

    def _assert_rejects(self, data: dict, fragment: str) -> None:
        with pytest.raises(CatalogError) as excinfo:
            parse_catalog(data)
        assert fragment in str(excinfo.value)

    def test_unknown_framework_reference(self):
        data = _raw_catalog()
        data["controls"][0]["mappings"]["eu_ai_act"] = ["Art. 999"]
        self._assert_rejects(data, "has no reference 'Art. 999'")

    def test_unknown_framework(self):
        data = _raw_catalog()
        data["controls"][0]["mappings"]["nist_csf"] = ["PR.AA-01"]
        self._assert_rejects(data, "unknown framework 'nist_csf'")

    def test_duplicate_id(self):
        data = _raw_catalog()
        data["controls"].append(copy.deepcopy(data["controls"][0]))
        self._assert_rejects(data, "duplicate id")

    def test_prefix_must_match_domain(self):
        data = _raw_catalog()
        data["controls"][0]["domain"] = "NET"
        self._assert_rejects(data, "does not match domain")

    def test_unknown_owasp_code(self):
        data = _raw_catalog()
        data["controls"][0]["mitigates"] = ["LLM99"]
        self._assert_rejects(data, "unknown OWASP code 'LLM99'")

    def test_unknown_stride_letter(self):
        data = _raw_catalog()
        data["controls"][0]["stride"] = ["X"]
        self._assert_rejects(data, "unknown STRIDE letter")

    def test_card_example_must_exist(self):
        data = _raw_catalog()
        data["cards"]["security_controls"]["example"] = ["IAM-99"]
        self._assert_rejects(data, "example id 'IAM-99'")

    def test_reports_every_problem_at_once(self):
        data = _raw_catalog()
        data["controls"][0]["mappings"]["eu_ai_act"] = ["Art. 999"]
        data["controls"][1]["mitigates"] = ["LLM99"]
        with pytest.raises(CatalogError) as excinfo:
            parse_catalog(data)
        assert "Art. 999" in str(excinfo.value)
        assert "LLM99" in str(excinfo.value)


# ---------------------------------------------------------------------------
# Reading CONTROLS off a threat
# ---------------------------------------------------------------------------


class TestSplitControlIds:
    @pytest.mark.parametrize(
        ("value", "known"),
        [
            (["IAM-05", "LOG-01"], ["IAM-05", "LOG-01"]),
            ("IAM-05, LOG-01", ["IAM-05", "LOG-01"]),
            (["iam-5"], ["IAM-05"]),
            (["IAM-05 (Secure JWT issuance and validation)"], ["IAM-05"]),
            ([{"id": "AGT-13"}], ["AGT-13"]),
            (["IAM-05", "IAM-05", "iam-05"], ["IAM-05"]),
            ("AI-01", ["AI-01"]),
        ],
    )
    def test_recovers_known_ids_from_model_shapes(self, value, known):
        assert split_control_ids(value)[0] == known

    def test_rejects_invented_ids_and_prose(self):
        known, rejected = split_control_ids(["IAM-05", "IAM-99", "XYZ-01", "see notes"])
        assert known == ["IAM-05"]
        assert "IAM-99" in rejected
        assert "XYZ-01" in rejected
        assert "see notes" in rejected

    @pytest.mark.parametrize("value", [None, "", [], 42, {"name": "no id"}])
    def test_empty_or_malformed_yields_nothing_known(self, value):
        assert normalize_control_ids(value) == []

    def test_keep_known_controls_rewrites_in_place(self):
        threat = {"CONTROLS": "iam-5, IAM-99"}
        keep_known_controls(threat)
        assert threat["CONTROLS"] == ["IAM-05"]

    def test_keep_known_controls_drops_key_when_nothing_is_valid(self):
        threat = {"CONTROLS": ["IAM-99"]}
        keep_known_controls(threat)
        assert "CONTROLS" not in threat


# ---------------------------------------------------------------------------
# Compliance summary
# ---------------------------------------------------------------------------


class TestComplianceSummary:
    def test_none_without_controls(self):
        assert compliance_summary([{"Threat Type": "Spoofing"}]) is None
        assert compliance_summary([{"CONTROLS": ["IAM-99"]}]) is None

    def test_counts_threats_per_control(self):
        summary = compliance_summary([WEB_THREAT, AGENT_THREAT])
        assert summary is not None
        counts = {use.control.id: use.threat_count for use in summary.controls}
        assert counts["IAM-05"] == 2
        assert counts["AGT-05"] == 1
        # Most-cited first.
        assert summary.controls[0].control.id == "IAM-05"

    def test_framework_refs_resolve_from_the_catalogue(self):
        catalog = load_catalog()
        summary = compliance_summary([AGENT_THREAT])
        assert summary is not None
        for coverage in summary.frameworks:
            for ref in coverage.refs:
                assert coverage.framework.has_ref(ref.ref)
                assert ref.title == coverage.framework.title(ref.ref)
                for cid in ref.control_ids:
                    assert ref.ref in catalog.control(cid).refs_for(coverage.framework.key)

    def test_web_report_omits_ai_frameworks(self):
        summary = compliance_summary([WEB_THREAT])
        assert summary is not None
        assert not summary.ai_scope
        assert {c.framework.key for c in summary.frameworks} == {"iso_27001"}
        assert {f.key for f in summary.omitted_frameworks} == AI_FRAMEWORKS

    def test_ai_report_includes_ai_frameworks(self):
        summary = compliance_summary([WEB_THREAT, AGENT_THREAT])
        assert summary is not None
        assert summary.ai_scope
        assert {c.framework.key for c in summary.frameworks} == AI_FRAMEWORKS | {"iso_27001"}
        assert summary.omitted_frameworks == []

    @pytest.mark.parametrize(
        "signal",
        [
            {"OWASP_LLM": "LLM01"},
            {"OWASP_ASI": "ASI01"},
            {"INSIDER_CATEGORY": "Data Exfiltration"},
            {"MITRE_ATTACK": [{"id": "AML.T0051", "name": "LLM Prompt Injection"}]},
            {"MITRE_ATTACK": "T1190, AML.T0051"},
            {"CONTROLS": ["AI-01"]},
        ],
    )
    def test_ai_scope_signals(self, signal):
        assert has_ai_scope([{"Threat Type": "Tampering", **signal}])

    def test_enterprise_mitre_alone_is_not_ai_scope(self):
        assert not has_ai_scope([{"MITRE_ATTACK": [{"id": "T1190"}], "CONTROLS": ["APP-02"]}])

    def test_ai_domains_match_the_ai_card(self):
        catalog = load_catalog()
        ai_card_domains = {d.key for d in catalog.domains if d.card == "ai_controls"}
        assert ai_card_domains == AI_DOMAINS

    def test_to_dict_is_json_serialisable(self):
        summary = compliance_summary([WEB_THREAT, AGENT_THREAT])
        assert summary is not None
        data = json.loads(json.dumps(summary.to_dict()))
        assert data["catalog_version"] == load_catalog().version
        assert {c["id"] for c in data["controls"]} == {"IAM-05", "LOG-01", "AGT-05", "AGT-07"}


class TestFrameworkRefs:
    def test_respects_ai_scope(self):
        assert set(framework_refs(["IAM-05"], ai_scope=False)) == {"iso_27001"}
        assert "eu_ai_act" in framework_refs(["IAM-05"], ai_scope=True)

    def test_refs_follow_registry_order_without_duplicates(self):
        refs = framework_refs(["LOG-01", "LOG-02", "AGT-11"], ai_scope=True)["eu_ai_act"]
        assert len(refs) == len(set(refs))
        order = [ref for ref, _ in load_catalog().framework("eu_ai_act").refs]
        assert refs == sorted(refs, key=order.index)


class TestComplianceRows:
    def test_one_row_per_threat_control_and_reference(self):
        rows = compliance_rows([WEB_THREAT])
        assert rows
        assert set(rows[0]) == set(COMPLIANCE_ROW_FIELDS)
        # A web report carries only ISO/IEC 27001 rows.
        assert {r["framework"] for r in rows} == {"ISO/IEC 27001"}
        assert {r["control_id"] for r in rows} == {"IAM-05", "LOG-01"}

    def test_control_without_a_reference_still_gets_a_row(self):
        """AGT-14 maps to no AIUC-1 requirement; it must not vanish from the
        AIUC-1 slice of the export."""
        threat = {"OWASP_ASI": "ASI08", "CONTROLS": ["AGT-14"]}
        aiuc = [r for r in compliance_rows([threat]) if r["framework"] == "AIUC-1"]
        assert aiuc == [{**aiuc[0], "reference": "", "requirement": ""}]

    @pytest.mark.parametrize("payload", ["=HYPERLINK(\"http://x\")", "+1", "-1", "@SUM(A1)"])
    def test_formula_injection_is_defused(self, payload):
        """Scenario text is model output, steerable by whoever wrote the
        application description; a spreadsheet must not evaluate it."""
        rows = compliance_rows([{**WEB_THREAT, "Scenario": payload}])
        assert all(r["scenario"] == "'" + payload for r in rows)
        assert spreadsheet_safe("normal text") == "normal text"


# ---------------------------------------------------------------------------
# Generated cards and docs
# ---------------------------------------------------------------------------


class TestGeneratedFiles:
    @pytest.mark.parametrize("relative", sorted(generated_files()))
    def test_committed_copy_matches_the_catalogue(self, relative):
        """Edit catalog.toml, then run scripts/build_control_catalog.py."""
        path = REPO_ROOT / relative
        assert path.exists(), f"{relative} is missing; run scripts/build_control_catalog.py"
        assert path.read_text(encoding="utf-8") == generated_files()[relative], (
            f"{relative} is out of date; run python scripts/build_control_catalog.py"
        )

    def test_cards_are_discoverable_and_add_controls(self):
        cards = {e["name"]: e for e in list_references()}
        for name in ("security_controls", "ai_controls"):
            assert "CONTROLS" in cards[name]["adds_fields"]
            assert cards[name]["version"] == load_catalog().version

    def test_each_card_lists_exactly_its_domains_controls(self):
        catalog = load_catalog()
        for card in catalog.cards:
            body = load_reference(card.name)
            mine = {c.id for c in catalog.controls_for_card(card.name)}
            assert mine
            for cid in mine:
                assert f"`{cid}`" in body, cid
            others = {c.id for c in catalog.controls} - mine
            assert not any(f"`{cid}`" in body for cid in others)

    def test_cards_never_show_the_model_framework_clauses(self):
        """The model picks controls; clauses are looked up. A clause in the
        card would invite the model to cite it."""
        catalog = load_catalog()
        for card in catalog.cards:
            body = load_reference(card.name)
            assert "Art. " not in body
            assert "A.5." not in body and "A.6.2" not in body
            assert "Anti-hallucination" in body


# ---------------------------------------------------------------------------
# Markdown / HTML / JSON / SARIF rendering
# ---------------------------------------------------------------------------


@pytest.fixture
def controls_report(sample_plan) -> AnalysisReport:
    return AnalysisReport(
        plan=sample_plan,
        findings=[
            SubsystemFinding(
                subsystem="Agent",
                threats=[copy.deepcopy(AGENT_THREAT), copy.deepcopy(WEB_THREAT)],
            )
        ],
        cross_cutting_threats=[{
            "Threat Type": "Repudiation",
            "Scenario": "Tool calls are not logged.",
            "Potential Impact": "No forensic trail.",
            "Affected Subsystems": ["Agent"],
            "CONTROLS": ["AGT-11"],
        }],
        metadata={"llm_calls": 3, "tool_calls": 4},
    )


class TestTableColumn:
    def test_controls_column_only_when_present(self):
        assert detect_extra_columns([{"Threat Type": "S"}]).show_controls is False
        assert detect_extra_columns([WEB_THREAT]).show_controls is True
        # An invented ID alone doesn't surface a blank column.
        assert detect_extra_columns([{"CONTROLS": ["IAM-99"]}]).show_controls is False

    def test_cell_shows_only_known_ids(self):
        cols = detect_extra_columns([WEB_THREAT])
        header, _ = threat_table_header(*cols)
        assert "| Controls |" in header
        row = threat_table_row({**WEB_THREAT, "CONTROLS": ["IAM-05", "IAM-99"]}, *cols)
        assert "IAM-05" in row
        assert "IAM-99" not in row


class TestComplianceMarkdown:
    def test_empty_without_controls(self):
        assert compliance_section_lines([{"Threat Type": "Spoofing"}]) == []

    def test_web_report_section(self):
        text = "\n".join(compliance_section_lines([WEB_THREAT]))
        assert "## Controls & Compliance Mapping" in text
        assert "### ISO/IEC 27001" in text
        assert "### EU AI Act" not in text
        assert "omitted because no threat in this report concerns an AI system" in text

    def test_ai_report_section_lists_framework_requirements(self):
        text = "\n".join(compliance_section_lines([AGENT_THREAT]))
        for heading in ("### AIUC-1", "### ISO/IEC 42001", "### EU AI Act", "### ISO/IEC 27001"):
            assert heading in text
        assert "Art. 14" in text  # AGT-07, human approval
        assert "D003" in text  # AGT-05, restrict unsafe tool calls

    def test_quick_renderer_includes_section(self):
        md = json_to_markdown([AGENT_THREAT], ["Describe the tools."])
        assert "| Controls |" in md
        assert "## Controls & Compliance Mapping" in md
        assert md.index("Controls & Compliance") < md.index("Improvement Suggestions")


class TestAgentReportRenderers:
    def test_markdown_live_and_replay(self, controls_report):
        live = render_markdown(controls_report)
        replay = render_markdown_from_json(render_json(controls_report))
        for md in (live, replay):
            assert "| Controls |" in md
            assert "## Controls & Compliance Mapping" in md
            assert md.index("Controls & Compliance") < md.index("## Summary")

    def test_json_carries_a_compliance_summary(self, controls_report):
        data = render_json(controls_report)
        assert data["compliance"]["ai_scope"] is True
        assert "AGT-11" in {c["id"] for c in data["compliance"]["controls"]}

    def test_json_without_controls_has_no_summary(self, sample_report):
        assert "compliance" not in render_json(sample_report)

    def test_sarif_properties(self, controls_report):
        results = render_sarif(controls_report)["runs"][0]["results"]
        agent = next(r for r in results if "refund" in r["message"]["text"])
        assert agent["properties"]["controls"] == ["AGT-05", "AGT-07", "IAM-05"]
        assert "Art. 14" in agent["properties"]["frameworks"]["eu_ai_act"]
        cross = next(r for r in results if r["properties"]["subsystem"] == "cross-cutting")
        assert cross["properties"]["controls"] == ["AGT-11"]

    def test_sarif_web_report_has_no_ai_framework_refs(self, sample_plan):
        report = AnalysisReport(
            plan=sample_plan,
            findings=[SubsystemFinding(subsystem="API", threats=[copy.deepcopy(WEB_THREAT)])],
        )
        result = render_sarif(report)["runs"][0]["results"][0]
        assert set(result["properties"]["frameworks"]) == {"iso_27001"}

    def test_html_pills_and_section(self, controls_report):
        page = render_html(controls_report)
        assert 'id="controls-compliance"' in page
        assert ">AGT-05<" in page
        assert "Prevent unauthorized AI agent actions" in page  # AIUC-1 B006 title

    def test_html_live_and_replay_identical(self, controls_report):
        assert render_html(controls_report) == render_html_from_json(render_json(controls_report))

    def test_html_never_renders_an_unvalidated_control(self, sample_plan):
        hostile = {**WEB_THREAT, "CONTROLS": ["IAM-05", "<script>alert(1)</script>"]}
        report = AnalysisReport(
            plan=sample_plan, findings=[SubsystemFinding(subsystem="API", threats=[hostile])]
        )
        page = render_html(report)
        assert "<script>alert(1)</script>" not in page
        assert ">IAM-05<" in page


# ---------------------------------------------------------------------------
# Agent loop, synthesis and /quick
# ---------------------------------------------------------------------------


class TestReportThreatControls:
    def test_tool_schema_offers_catalogue_ids(self):
        tool = next(t["function"] for t in REPORTING_TOOLS if t["function"]["name"] == "report_threat")
        controls = tool["parameters"]["properties"]["controls"]
        assert controls["items"]["enum"] == load_catalog().control_ids
        assert THREAT_ARG_TO_FIELD["controls"] == "CONTROLS"

    def test_invented_ids_are_dropped_and_reported_back(self):
        threat = {"CONTROLS": ["IAM-05", "IAM-99", "iam-6"]}
        note = _apply_control_ids(threat)
        assert threat["CONTROLS"] == ["IAM-05", "IAM-06"]
        assert "IAM-99" in note

    def test_all_invalid_removes_the_field(self):
        threat = {"CONTROLS": ["NOPE"]}
        note = _apply_control_ids(threat)
        assert "CONTROLS" not in threat
        assert "NOPE" in note

    def test_valid_ids_add_no_note(self):
        threat = {"CONTROLS": ["IAM-05"]}
        assert _apply_control_ids(threat) == ""

    def test_through_the_subsystem_loop(self, model_pair, sandbox_dir):
        """End to end: the recorded threat keeps only catalogue IDs and the
        tool result tells the model which one it invented."""
        from unittest.mock import MagicMock

        from stride_gpt.agent.loop import _analyze_subsystem
        from tests.fakes import SUBSYSTEM_TOOL_NAMES

        report = ToolCallResult(
            id="r1",
            function_name="report_threat",
            arguments={
                "threat_type": "Spoofing",
                "scenario": "Tokens are not validated",
                "potential_impact": "Takeover",
                "evidence": [],
                "controls": ["IAM-05", "IAM-77"],
            },
        )
        finish = ToolCallResult(id="f1", function_name="finish", arguments={"improvement_suggestions": []})
        ctx = MagicMock()
        ctx.needs_compression.return_value = False
        with ScriptedLLM([call_tools(report, finish, tools=SUBSYSTEM_TOOL_NAMES)]) as fake:
            finding = _analyze_subsystem(
                models=model_pair, target_path=sandbox_dir, subsystem_name="App",
                subsystem_description="Main app", key_files=[], focus_areas=[],
                ctx=ctx, max_llm_calls=0, max_tool_calls=0,
                progress=MagicMock(), call_counts={},
            )
        assert finding.threats[0]["CONTROLS"] == ["IAM-05"]
        assert len(fake.requests) == 1

    def test_synthesis_items_are_sanitised(self, sandbox_dir):
        findings = [SubsystemFinding(
            subsystem="Auth",
            threats=[{"id": "t1", "Threat Type": "Spoofing", "Scenario": "s", "Potential Impact": "i"}],
        )]
        raw = [{
            "Classification": "aggregation",
            "Threat Type": "Spoofing",
            "Scenario": "No authentication anywhere",
            "Related Threats": ["t1"],
            "CONTROLS": ["IAM-01", "MADE-UP-1"],
        }]
        _emergent, aggregations = classify_synthesis(raw, findings, sandbox_dir)
        assert aggregations[0]["CONTROLS"] == ["IAM-01"]


class TestQuickControls:
    def test_parse_drops_unknown_ids(self):
        output = _parse_threat_model(json.dumps({
            "threat_model": [
                {"Threat Type": "Spoofing", "Scenario": "s", "Potential Impact": "i",
                 "CONTROLS": ["IAM-05", "IAM-99"]},
                {"Threat Type": "Tampering", "Scenario": "t", "Potential Impact": "i",
                 "CONTROLS": ["nonsense"]},
            ],
            "improvement_suggestions": [],
        }))
        assert output is not None
        assert output.threat_model[0]["CONTROLS"] == ["IAM-05"]
        assert "CONTROLS" not in output.threat_model[1]

    def test_end_to_end_with_card_load_and_saved_summary(self, model_pair):
        load = ToolCallResult(id="l1", function_name="load_reference",
                              arguments={"name": "security_controls"})
        final = json.dumps({
            "threat_model": [copy.deepcopy(WEB_THREAT)],
            "improvement_suggestions": [],
        })
        with ScriptedLLM([
            call_tools(load, tools=QUICK_TOOL_NAMES),
            reply(final, tools=QUICK_TOOL_NAMES),
        ]) as fake:
            output = run_quick_analysis(model_pair, "A web API using JWT bearer tokens.")
        assert output.references_loaded == ["security_controls"]
        tool_result = next(m for m in fake.requests[1].messages if m["role"] == "tool")
        assert "IAM-05" in tool_result["content"]

        saved = json.loads(save_quick_report(output, "api", models=model_pair).read_text())
        assert saved["compliance"]["ai_scope"] is False
        assert [f["key"] for f in saved["compliance"]["frameworks"]] == ["iso_27001"]


# ---------------------------------------------------------------------------
# Legacy single-shot prompt (web UI)
# ---------------------------------------------------------------------------


class TestThreatModelPrompt:
    def _prompt(self, app_type: str, **kwargs) -> str:
        return create_threat_model_prompt(app_type, "OAUTH2", "Yes", "Confidential", "An app.", **kwargs)

    def test_off_by_default(self):
        prompt = self._prompt("Web application")
        assert "CONTROLS" not in prompt

    def test_web_app_gets_the_security_card_only(self):
        prompt = self._prompt("Web application", include_controls=True)
        assert '"CONTROLS"' in prompt
        assert "`IAM-05`" in prompt
        assert "`AGT-05`" not in prompt

    @pytest.mark.parametrize("app_type", ["Generative AI application", "Agentic AI application"])
    def test_ai_apps_get_both_cards(self, app_type):
        prompt = self._prompt(app_type, include_controls=True)
        assert "`IAM-05`" in prompt
        assert "`AGT-05`" in prompt


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


runner = CliRunner()


class TestControlsCommand:
    def test_lists_the_catalogue(self):
        result = runner.invoke(cli.app, ["controls"], env={"COLUMNS": "200"})
        assert result.exit_code == 0
        assert "IAM-01" in result.stdout
        assert "AGT-14" in result.stdout

    def test_domain_filter(self):
        result = runner.invoke(cli.app, ["controls", "-d", "net"], env={"COLUMNS": "200"})
        assert result.exit_code == 0
        assert "NET-03" in result.stdout
        assert "IAM-01" not in result.stdout

    def test_unknown_domain(self):
        result = runner.invoke(cli.app, ["controls", "-d", "nope"])
        assert result.exit_code == 1

    def test_shows_one_control(self):
        result = runner.invoke(cli.app, ["controls", "agt-13"], env={"COLUMNS": "200"})
        assert result.exit_code == 0
        assert "Kill switch" in result.stdout
        assert "Art. 14(4)(e)" in result.stdout

    def test_unknown_control(self):
        result = runner.invoke(cli.app, ["controls", "IAM-99"])
        assert result.exit_code == 1

    def test_framework_crosswalk(self):
        result = runner.invoke(cli.app, ["controls", "--framework", "eu-ai-act"], env={"COLUMNS": "200"})
        assert result.exit_code == 0
        assert "Art. 14(4)(e)" in result.stdout
        assert "AGT-13" in result.stdout

    def test_output_requires_report(self, tmp_path):
        result = runner.invoke(cli.app, ["controls", "-o", str(tmp_path / "x.csv")])
        assert result.exit_code == 2

    def _saved_report(self, tmp_path: Path, threats: list[dict]) -> Path:
        path = tmp_path / "report.json"
        path.write_text(json.dumps({
            "subsystems": [{"name": "Application", "threats": threats}],
            "cross_cutting_threats": [],
        }))
        return path

    def test_exports_csv(self, tmp_path):
        report = self._saved_report(tmp_path, [AGENT_THREAT])
        out = tmp_path / "out" / "mapping.csv"
        result = runner.invoke(cli.app, ["controls", "--report", str(report), "-o", str(out)])
        assert result.exit_code == 0, result.stdout
        rows = list(csv.DictReader(io.StringIO(out.read_text())))
        assert tuple(rows[0]) == COMPLIANCE_ROW_FIELDS
        assert {"AIUC-1", "EU AI Act"} <= {r["framework"] for r in rows}

    def test_exports_json(self, tmp_path):
        report = self._saved_report(tmp_path, [AGENT_THREAT])
        out = tmp_path / "mapping.json"
        result = runner.invoke(cli.app, ["controls", "--report", str(report), "-o", str(out)])
        assert result.exit_code == 0
        assert json.loads(out.read_text())["ai_scope"] is True

    def test_report_without_controls(self, tmp_path):
        report = self._saved_report(tmp_path, [{"Threat Type": "Spoofing"}])
        result = runner.invoke(cli.app, ["controls", "--report", str(report)])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# Streamlit web UI helpers (apps/web)
# ---------------------------------------------------------------------------


class TestWebHelpers:
    def test_threat_table_uses_shared_columns(self):
        from threat_model import json_to_markdown as web_json_to_markdown

        md = web_json_to_markdown(
            [{**AGENT_THREAT, "INSIDER_CATEGORY": "Credential Compromise"}],
            ["Say which tools need approval | then"],
        )
        assert "| Controls |" in md
        assert "| Insider Category |" in md
        # The compliance section lives on its own tab, not in the threat table.
        assert "Compliance Mapping" not in md
        # Suggestions stay escaped.
        assert "approval \\| then" in md

    def test_mitigations_prompt_cites_controls_only_when_present(self):
        from mitigations import create_mitigations_prompt
        from threat_model import json_to_markdown as web_json_to_markdown

        with_controls = create_mitigations_prompt(web_json_to_markdown([AGENT_THREAT], []))
        without = create_mitigations_prompt(
            web_json_to_markdown([{"Threat Type": "S", "Scenario": "s", "Potential Impact": "i"}], [])
        )
        assert "cite their IDs" in with_controls
        assert "cite their IDs" not in without
