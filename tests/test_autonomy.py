"""Keep CLI, web and packaged guidance on the same approval/initiative scale."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from stride_gpt.agent.loop import _SubsystemRun, classify_synthesis
from stride_gpt.agent.report import load_report
from stride_gpt.agent.tools import REPORTING_TOOLS
from stride_gpt.core.autonomy import (
    AUTONOMY_DESCRIPTIONS,
    AUTONOMY_LABELS,
    AUTONOMY_LEVELS,
    AUTONOMY_SCHEMA_DESCRIPTION,
    AUTONOMY_TAXONOMY,
    autonomy_scale_markdown,
    normalize_generated_autonomy,
)
from stride_gpt.core.prompts.builder import create_insider_threat_prompt_section
from stride_gpt.core.prompts.variants import load_reference
from stride_gpt.core.schemas import SubsystemFinding, ToolCallResult
from stride_gpt.core.threat_model import THREAT_MODEL_SCHEMA, validate_threat_model_data

ROOT = Path(__file__).resolve().parents[1]


def test_shadow_scan_names_and_level_order():
    assert list(AUTONOMY_LABELS.items()) == [
        ("L0", "Chatbot"),
        ("L1", "Copilot"),
        ("L2", "Supervised"),
        ("L3", "Semi-Autonomous / Agentic Workflow"),
        ("L4", "High Autonomy"),
        ("L5", "Fully Autonomous"),
    ]
    assert set(AUTONOMY_DESCRIPTIONS) == set(AUTONOMY_LEVELS)


def test_cli_and_single_shot_schemas_use_one_scale_and_allow_unknown_omission():
    report_tool = next(t["function"] for t in REPORTING_TOOLS
                       if t["function"]["name"] == "report_threat")
    tool_params = report_tool["parameters"]
    web_params = THREAT_MODEL_SCHEMA["properties"]["threat_model"]["items"]
    assert tool_params["properties"]["autonomy_level"]["enum"] == AUTONOMY_LEVELS
    assert web_params["properties"]["autonomy_level"]["enum"] == [*AUTONOMY_LEVELS, None]
    for params in (tool_params, web_params):
        assert "autonomy_level" not in params["required"]
        assert params["properties"]["autonomy_level"]["description"] == AUTONOMY_SCHEMA_DESCRIPTION


@pytest.mark.parametrize("path", ["README.md", "docs/agentic-ai-controls.md"])
def test_documentation_defines_the_same_six_levels(path):
    rows = (ROOT / path).read_text().splitlines()
    for level, label in AUTONOMY_LABELS.items():
        assert any(row.startswith(f"| **{level}** | {label} |") for row in rows)


def test_reference_card_reaches_both_analysis_paths_with_no_unknown_default():
    card = load_reference("insider_threat")
    assert card in create_insider_threat_prompt_section()
    for level, label in AUTONOMY_LABELS.items():
        assert f"**{level} — {label}**" in card
    assert "omit `autonomy_level`" in card
    assert "scheduled workflow with an approval gate is not L5" in card
    assert "Read-only retrieval within a person's session is L1" in card
    assert "assume L2/L3 for any system" not in card


def test_web_guidance_distinguishes_side_effect_approval_from_self_initiation():
    table = autonomy_scale_markdown()
    assert "| L0 | Chatbot | Answers only; no tools or actions." in table
    assert "| L1 | Copilot |" in table and "read-only tools" in table
    assert "approves each side-effecting tool action" in table
    assert "approval is at checkpoints, not per action" in table
    assert "Starts itself through an event, schedule or another agent" in table
    assert "People only monitor" in table


@pytest.mark.parametrize("level", AUTONOMY_LEVELS)
def test_generated_levels_receive_application_owned_taxonomy_without_mutating_input(level):
    original = {"autonomy_level": level, "autonomy_taxonomy": "model-invented/v9"}
    result = normalize_generated_autonomy(original)
    assert result == {"autonomy_level": level, "autonomy_taxonomy": AUTONOMY_TAXONOMY}
    assert original["autonomy_taxonomy"] == "model-invented/v9"


@pytest.mark.parametrize("level", [None, "", "unknown", "L6", "L1 Copilot", 1, True, [], {}])
def test_invalid_generated_levels_and_untrusted_taxonomy_are_removed(level):
    result = normalize_generated_autonomy({
        "Scenario": "preserved", "autonomy_level": level,
        "autonomy_taxonomy": AUTONOMY_TAXONOMY,
    })
    assert result == {"Scenario": "preserved"}
    assert normalize_generated_autonomy({"autonomy_taxonomy": "forged"}) == {}


@pytest.mark.parametrize("level", ["L0", "L5", None, "L6", ["L2"]])
@pytest.mark.parametrize("ingestion", ["tool", "text-fallback", "single-shot", "synthesis"])
def test_generation_ingestion_uses_validated_taxonomy(tmp_path, level, ingestion):
    threat = {
        "Threat Type": "Tampering", "Scenario": "changed source", "Potential Impact": "integrity",
        "autonomy_level": level, "autonomy_taxonomy": "untrusted-scale/v42",
    }
    if ingestion == "single-shot":
        result = validate_threat_model_data({"threat_model": [threat]}).threat_model[0]
    elif ingestion == "synthesis":
        legacy = {"id": "app-T1", "autonomy_level": "L1"}
        finding = SubsystemFinding(subsystem="App", threats=[legacy])
        raw = {**threat, "Classification": "aggregation", "Related Threats": ["app-T1"]}
        _, aggregations = classify_synthesis([raw], [finding], tmp_path)
        result = aggregations[0]
        # Reusing a historical finding does not relabel its level.
        assert finding.threats == [legacy]
        assert "autonomy_taxonomy" not in legacy
    else:
        run = _SubsystemRun(
            target_path=tmp_path, subsystem_name="App", progress=Mock(),
            max_tool_calls=0, loaded_refs=None,
        )
        if ingestion == "tool":
            run.handle(ToolCallResult(
                id="report", function_name="report_threat", arguments=threat,
            ))
        else:
            assert run.take_text_fallback(json.dumps({"threats": [threat]}))
        result = run.threats[0]
    if level in ("L0", "L5"):
        assert result["autonomy_level"] == level
        assert result["autonomy_taxonomy"] == AUTONOMY_TAXONOMY
    else:
        assert "autonomy_level" not in result
        assert "autonomy_taxonomy" not in result


def test_loading_historical_reports_preserves_original_autonomy_without_relabelling(tmp_path):
    original = {"findings": [{"threats": [
        {"autonomy_level": "L1"},
        {"autonomy_level": "L4", "autonomy_taxonomy": "legacy-deployment-archetypes/v1"},
    ]}]}
    path = tmp_path / "historical.json"
    path.write_text(json.dumps(original))
    assert load_report(path) == original
    assert json.loads(path.read_text()) == original
