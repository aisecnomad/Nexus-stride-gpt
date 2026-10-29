"""Untrusted annotations must agree across ingest and export boundaries."""

import json

import pytest

from stride_gpt.agent.quick import _parse_threat_model
from stride_gpt.agent.report import render_json, render_sarif
from stride_gpt.core.controls import has_ai_scope
from stride_gpt.core.mitre import normalize_techniques, normalize_threat_mitre, technique_catalog
from stride_gpt.core.threat_model import _parse_threat_model_response


@pytest.mark.parametrize("value", [
    "T9999, AML.fabricated, T1fabricated",
    ["T9999", "AML.fabricated", "T1fabricated"],
    [{"id": "T9999", "name": "Invented"}, {"id": "NOT_A_TECHNIQUE"}],
    [{"id": "T1078.004", "name": "Unlisted sub-technique"}],
])
def test_unknown_ids_are_rejected_in_every_supported_shape(value):
    assert normalize_techniques(value) == []


def test_catalogue_names_override_model_names_and_deduplicate():
    assert normalize_techniques([
        {"id": "T1190", "name": "Invented hostile name"}, "T1190", "AML.T0051",
    ]) == [
        ("T1190", "Exploit Public-Facing Application"),
        ("AML.T0051", "LLM Prompt Injection"),
    ]
    assert len(technique_catalog()) > 250


@pytest.mark.parametrize("parse", [_parse_threat_model, _parse_threat_model_response])
def test_model_ingestion_uses_validated_names(parse):
    payload = {"threat_model": [{"Threat Type": "Tampering", "Scenario": "s", "Potential Impact": "i",
                                "MITRE_ATTACK": [{"id": "T1190", "name": "Forged"}, {"id": "T9999"}]}]}
    parsed = parse(json.dumps(payload))
    assert parsed.threat_model[0]["MITRE_ATTACK"] == [
        {"id": "T1190", "name": "Exploit Public-Facing Application"}
    ]


def test_json_and_sarif_never_export_unknown_techniques(sample_report):
    sample_report.findings[0].threats[0]["MITRE_ATTACK"] = [
        {"id": "T1190", "name": "Forged"}, {"id": "T9999", "name": "Invented"},
    ]
    data = render_json(sample_report)
    assert data["subsystems"][0]["threats"][0]["MITRE_ATTACK"] == [
        {"id": "T1190", "name": "Exploit Public-Facing Application"}
    ]
    sarif = render_sarif(sample_report)
    assert sarif["runs"][0]["results"][0]["properties"]["mitre_attack"] == ["T1190"]
    assert "T9999" not in json.dumps(data)
    assert "T9999" not in json.dumps(sarif)


def test_fabricated_atlas_annotation_does_not_create_ai_scope():
    assert not has_ai_scope([{"MITRE_ATTACK": [{"id": "AML.fabricated"}]}])
    assert has_ai_scope([{"MITRE_ATTACK": [{"id": "AML.T0051"}]}])


def test_normalization_does_not_modify_the_original_threat():
    threat = {"MITRE_ATTACK": [{"id": "T1190", "name": "Forged"}]}
    normalized = normalize_threat_mitre(threat)
    assert threat["MITRE_ATTACK"][0]["name"] == "Forged"
    assert normalized["MITRE_ATTACK"][0]["name"] == "Exploit Public-Facing Application"


def test_malformed_entries_cannot_bypass_catalogue_membership():
    assert normalize_techniques([
        None, 1190, ["T1190"], {"id": ["T1190"]}, {"id": None},
        {"id": "T1190\n![leak](https://attacker.invalid)"},
        {"id": "T1190", "name": '<img src="https://attacker.invalid">'},
    ]) == [("T1190", "Exploit Public-Facing Application")]


@pytest.mark.parametrize("card", ["", "- **T1190** — First name\n- **T1190** — Other name\n"])
def test_broken_packaged_catalogues_fail_closed(tmp_path, monkeypatch, card):
    import stride_gpt.core.mitre as mitre

    (tmp_path / "mitre_enterprise.md").write_text(card)
    (tmp_path / "mitre_atlas.md").write_text("- **AML.T0051** — LLM Prompt Injection\n")
    monkeypatch.setattr(mitre, "files", lambda package: tmp_path)
    technique_catalog.cache_clear()
    try:
        with pytest.raises(ValueError, match=r"no techniques|Conflicting"):
            normalize_techniques(["T1190"])
    finally:
        technique_catalog.cache_clear()
