"""Tests for stride_gpt.core.threat_model parsing helpers.

Focus on the resilience path: local models frequently emit prose or
fence-wrapped JSON instead of a clean object, so the parser must clean common
noise and, on genuine failure, return a well-formed ThreatModelOutput carrying
a structured error rather than raising into the caller.
"""

from __future__ import annotations

import json

import pytest

from stride_gpt.core.threat_model import (
    _clean_json_content,
    _parse_threat_model_response,
)


class TestParseThreatModelResponse:
    def test_parses_valid_json(self):
        content = (
            '{"threat_model": [{"Threat Type": "Spoofing", "Scenario": "s", '
            '"Potential Impact": "i"}], "improvement_suggestions": ["fix it"]}'
        )
        parsed = _parse_threat_model_response(content)
        assert parsed.threat_model[0]["Threat Type"] == "Spoofing"
        assert parsed.improvement_suggestions == ["fix it"]

    def test_malformed_json_yields_structured_error(self):
        parsed = _parse_threat_model_response("the model rambled instead {{{")
        assert len(parsed.threat_model) == 1
        assert parsed.threat_model[0]["Threat Type"] == "Error"
        assert "Failed to parse" in parsed.threat_model[0]["Scenario"]

    def test_error_fallback_includes_raw_snippet(self):
        parsed = _parse_threat_model_response("not json <b>hi</b>")
        joined = " ".join(parsed.improvement_suggestions)
        assert "JSON parse error" in joined
        assert "not json" in joined

    def test_error_snippet_escapes_pipes_for_markdown_table(self):
        # The snippet lands in a markdown table cell; unescaped pipes would
        # break the table layout.
        parsed = _parse_threat_model_response("a | b | c not json {{{")
        joined = " ".join(parsed.improvement_suggestions)
        assert "\\|" in joined

    def test_empty_response_reports_empty_placeholder(self):
        parsed = _parse_threat_model_response("")
        joined = " ".join(parsed.improvement_suggestions)
        assert "(empty response)" in joined

    def test_long_snippet_is_truncated(self):
        parsed = _parse_threat_model_response("x" * 1000 + " not json {{{")
        joined = " ".join(parsed.improvement_suggestions)
        assert "..." in joined

    def test_missing_keys_default_to_empty_lists(self):
        parsed = _parse_threat_model_response('{"threat_model": []}')
        assert parsed.threat_model == []
        assert parsed.improvement_suggestions == []

    @pytest.mark.parametrize("value", [
        [], None, "text", 1,
        {"threat_model": None},
        {"threat_model": "not an array"},
        {"threat_model": [None]},
        {"threat_model": ["not an object"]},
        {"threat_model": [{"Threat Type": "Spoofing"}]},
        {"threat_model": [{"Threat Type": "Spoofing", "Scenario": [], "Potential Impact": "i"}]},
        {"improvement_suggestions": "not an array"},
        {"improvement_suggestions": [None]},
    ])
    def test_wrong_json_shapes_return_explicit_errors(self, value):
        parsed = _parse_threat_model_response(json.dumps(value))
        assert parsed.threat_model[0]["Threat Type"] == "Error"
        assert any("JSON schema error" in item for item in parsed.improvement_suggestions)

    @pytest.mark.parametrize("scenario", [
        "Requests to https://example.com/api expose data",
        'A quoted \\"value\\" and // ordinary string text',
        "Example code: ```json\\n[1,\\n]\\n```",
        "A backslash before a URL: \\" + "https://example.com/api",
        "https://example.com/a?one=1&two=2 // text ending at EOF",
    ])
    def test_valid_json_preserves_urls_escapes_and_fences(self, scenario):
        content = json.dumps({
            "threat_model": [{"Threat Type": "Information Disclosure", "Scenario": scenario,
                              "Potential Impact": "i"}],
            "improvement_suggestions": ["Use https://example.com/docs"],
        }, indent=2)
        parsed = _parse_threat_model_response(content)
        assert parsed.threat_model[0]["Scenario"] == scenario
        assert parsed.improvement_suggestions == ["Use https://example.com/docs"]
        assert _clean_json_content(content) == content


class TestCleanJsonContent:
    def test_strips_json_fence(self):
        assert _clean_json_content('```json\n{"a": 1}\n```') == '{"a": 1}'

    def test_strips_bare_fence(self):
        assert _clean_json_content('```\n{"a": 1}\n```') == '{"a": 1}'

    def test_removes_line_comments(self):
        cleaned = _clean_json_content('{"a": 1} // a comment\n')
        assert "//" not in cleaned

    def test_repairs_trailing_comma_before_bracket(self):
        cleaned = _clean_json_content('{"x": [1,\n]}')
        assert ",\n]" not in cleaned

    def test_fenced_json_with_comment_becomes_parseable(self):
        raw = '```json\n{"threat_model": [], // note\n"improvement_suggestions": []}\n```'
        cleaned = _clean_json_content(raw)
        assert json.loads(cleaned) == {
            "threat_model": [],
            "improvement_suggestions": [],
        }

    def test_recovery_preserves_quoted_urls_and_comment_markers(self):
        raw = '''```json
{
  "threat_model": [{
    "Threat Type": "Spoofing", // model note
    "Scenario": "Visit https://example.com/ and read // comments",
    "Potential Impact": "i",
  },],
  "improvement_suggestions": ["Keep https://example.com/docs",],
} // final comment
```'''
        parsed = _parse_threat_model_response(raw)
        assert parsed.threat_model[0]["Scenario"] == "Visit https://example.com/ and read // comments"
        assert parsed.improvement_suggestions == ["Keep https://example.com/docs"]

    def test_json_string_fences_are_not_removed_during_recovery(self):
        raw = '{"example": "```json {\\"a\\":1} ```", "url": "https://example.com",}'
        assert json.loads(_clean_json_content(raw)) == {
            "example": '```json {"a":1} ```', "url": "https://example.com",
        }
