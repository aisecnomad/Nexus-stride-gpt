"""Tests for stride_gpt.agent.quick — description-driven threat model loop."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from stride_gpt.agent.quick import (
    QUICK_TOOLS,
    _build_user_content,
    _parse_threat_model,
    _retry_as_json,
    _strip_tool_artifacts,
    run_quick_analysis,
)
from stride_gpt.core.schemas import LLMResponse, ToolCallResult
from tests.fakes import QUICK_TOOL_NAMES, ScriptedLLM, call_tools, reply

# ---------------------------------------------------------------------------
# Tool set
# ---------------------------------------------------------------------------


class TestQuickTools:
    def test_only_reference_tools(self):
        """Quick analysis must not expose filesystem tools — there's no
        codebase, so read_file / grep / list_directory would be invitations to
        hallucinate. Restrict to the reference-card tools."""
        names = {t["function"]["name"] for t in QUICK_TOOLS}
        assert names == {"load_reference", "list_references"}

    @pytest.mark.parametrize(
        "name,arguments",
        [
            ("read_file", {}),
            ("grep_content", {"pattern": "PRIVATE_"}),
            ("list_directory", {}),
            ("search_files", {"pattern": "*"}),
            ("unknown_tool", {}),
        ],
    )
    def test_unadvertised_tool_is_denied_without_filesystem_access(
        self, name, arguments, tmp_path, model_pair, monkeypatch
    ):
        """A malicious model response cannot grant itself extra capabilities."""
        secret = tmp_path / "private.txt"
        secret.write_text("PRIVATE_SENTINEL")
        arguments = {**arguments, "path": str(secret)}

        def filesystem_access(*args, **kwargs):
            pytest.fail("quick analysis reached the filesystem executor")

        monkeypatch.setattr("stride_gpt.agent.tools.execute_tool", filesystem_access)
        steps = [
            call_tools(ToolCallResult("denied", name, arguments), tools=QUICK_TOOL_NAMES),
            call_tools(
                ToolCallResult("allowed", "load_reference", {"name": "genai"}),
                tools=QUICK_TOOL_NAMES,
            ),
            reply('{"threat_model":[],"improvement_suggestions":[]}', tools=QUICK_TOOL_NAMES),
        ]
        with ScriptedLLM(steps) as fake:
            output = run_quick_analysis(model_pair, "Review the application description.")

        denied = [m for m in fake.requests[1].messages if m["role"] == "tool"]
        assert len(denied) == 1
        assert denied[0]["tool_call_id"] == "denied"
        assert "not available in quick analysis" in denied[0]["content"]
        assert "PRIVATE_SENTINEL" not in json.dumps(fake.requests[-1].messages)
        assert output.references_loaded == ["genai"]
        assert output.tool_calls == 2


# ---------------------------------------------------------------------------
# User content construction (hint vs no hint)
# ---------------------------------------------------------------------------


class TestUserContent:
    def test_no_hint(self):
        text = _build_user_content("A flask app.", None)
        assert "A flask app." in text
        assert "hint" not in text.lower()

    def test_hint_included(self):
        text = _build_user_content("A LangGraph agent.", "Agentic AI application")
        assert "Agentic AI application" in text
        assert "A LangGraph agent." in text


# ---------------------------------------------------------------------------
# Loop behaviour
# ---------------------------------------------------------------------------


def _final_response(threats=None, suggestions=None) -> LLMResponse:
    payload = json.dumps({
        "threat_model": threats or [],
        "improvement_suggestions": suggestions or [],
    })
    return LLMResponse(content=payload, thinking=None, reasoning=None,
                       model="t", tool_calls=None)


class TestRunQuickAnalysis:
    @patch("stride_gpt.agent.quick.call_llm_with_tools")
    def test_single_turn_emits_threats(self, mock_tools, model_pair):
        """A web-shaped description should produce findings in one turn —
        the model has no reason to load LLM/agentic reference cards."""
        mock_tools.return_value = _final_response(
            threats=[{"Threat Type": "Spoofing", "Scenario": "s", "Potential Impact": "i"}],
            suggestions=["clarify auth"],
        )
        out = run_quick_analysis(model_pair, "A Flask CRUD app.")
        assert len(out.threat_model) == 1
        assert out.improvement_suggestions == ["clarify auth"]
        assert mock_tools.call_count == 1

    @patch("stride_gpt.agent.quick.call_llm_with_tools")
    def test_two_turn_with_load_reference(self, mock_tools, model_pair):
        """End-to-end: agent calls load_reference, then on the next turn emits
        a threat carrying an OWASP_LLM code derived from the loaded card."""
        turn1 = LLMResponse(
            content="I'll load the genai card first.",
            thinking=None, reasoning=None, model="t",
            tool_calls=[ToolCallResult(
                id="tc1", function_name="load_reference",
                arguments={"name": "genai"},
            )],
        )
        turn2 = _final_response(threats=[{
            "Threat Type": "Tampering",
            "Scenario": "Prompt injection via uploaded doc",
            "Potential Impact": "Bad",
            "OWASP_LLM": "LLM01",
        }])
        mock_tools.side_effect = [turn1, turn2]

        out = run_quick_analysis(model_pair, "A RAG-backed chatbot using OpenAI.")
        assert mock_tools.call_count == 2
        assert out.threat_model[0]["OWASP_LLM"] == "LLM01"
        # The tool result should be in the messages list on the second call.
        second_messages = mock_tools.call_args_list[1].args[1]
        tool_results = [m for m in second_messages if m.get("role") == "tool"]
        assert any("LLM01" in m["content"] for m in tool_results)

    @patch("stride_gpt.agent.quick.call_llm_with_tools")
    def test_repeated_load_reference_uses_cache(self, mock_tools, model_pair):
        """If the model calls load_reference for the same card twice in one
        turn, the second call should be served from cache, not re-execute the
        tool. Stops the model burning context on duplicated 13 KB cards."""
        turn1 = LLMResponse(
            content="",
            thinking=None, reasoning=None, model="t",
            tool_calls=[
                ToolCallResult(id="tc1", function_name="load_reference",
                               arguments={"name": "genai"}),
                ToolCallResult(id="tc2", function_name="load_reference",
                               arguments={"name": "genai"}),
            ],
        )
        turn2 = _final_response()
        mock_tools.side_effect = [turn1, turn2]

        run_quick_analysis(model_pair, "Any description.")
        # Inspect tool messages in the second call's message list.
        msgs = mock_tools.call_args_list[1].args[1]
        tool_msgs = [m for m in msgs if m.get("role") == "tool"]
        assert len(tool_msgs) == 2
        # First is the real card; second should be the cache-hit notice.
        assert "LLM01" in tool_msgs[0]["content"]
        assert "already loaded" in tool_msgs[1]["content"]

    @patch("stride_gpt.agent.quick.call_llm")
    @patch("stride_gpt.agent.quick.call_llm_with_tools")
    def test_bad_json_triggers_retry(self, mock_tools, mock_llm, model_pair):
        """If the model's final response isn't parseable JSON, we retry once
        with forced JSON mode."""
        mock_tools.return_value = LLMResponse(
            content="Sorry I cannot answer in JSON.",
            thinking=None, reasoning=None, model="t", tool_calls=None,
        )
        mock_llm.return_value = LLMResponse(
            content=json.dumps({
                "threat_model": [{"Threat Type": "Spoofing", "Scenario": "x", "Potential Impact": "y"}],
                "improvement_suggestions": [],
            }),
            thinking=None, reasoning=None, model="t",
        )
        out = run_quick_analysis(model_pair, "Anything.")
        assert mock_llm.call_count == 1
        assert len(out.threat_model) == 1

    @patch("stride_gpt.agent.quick.call_llm_with_tools")
    def test_records_call_counts_and_tool_breakdown(self, mock_tools, model_pair):
        """Output must record llm_calls, tool_calls, and a per-tool breakdown.
        Without these, a model that skips list_references / load_reference is
        invisible in the saved report — exactly the bug that motivated this."""
        turn1 = LLMResponse(
            content="discovering",
            thinking=None, reasoning=None, model="t",
            tool_calls=[ToolCallResult(
                id="t1", function_name="list_references", arguments={},
            )],
        )
        turn2 = LLMResponse(
            content="loading",
            thinking=None, reasoning=None, model="t",
            tool_calls=[ToolCallResult(
                id="t2", function_name="load_reference",
                arguments={"name": "genai"},
            )],
        )
        turn3 = _final_response()
        mock_tools.side_effect = [turn1, turn2, turn3]

        out = run_quick_analysis(model_pair, "A RAG chatbot.")

        assert out.llm_calls == 3
        assert out.tool_calls == 2
        assert out.tools_used == {"list_references": 1, "load_reference": 1}

    @patch("stride_gpt.agent.quick.call_llm_with_tools")
    def test_zero_tool_calls_recorded_when_model_skips_discovery(
        self, mock_tools, model_pair,
    ):
        """When the model emits a final JSON directly without loading any
        cards, tool_calls is 0 and tools_used is empty — the smoking gun for
        the discovery-skip regression should be unambiguous in the report."""
        mock_tools.return_value = _final_response()
        out = run_quick_analysis(model_pair, "A LangGraph agent.")
        assert out.llm_calls == 1
        assert out.tool_calls == 0
        assert out.tools_used == {}

    @patch("stride_gpt.agent.quick.call_llm")
    @patch("stride_gpt.agent.quick.call_llm_with_tools")
    def test_hits_max_llm_calls_coerces_final(self, mock_tools, mock_llm, model_pair):
        """If the model keeps calling tools forever, we cap it and force a
        final JSON output."""
        looper = LLMResponse(
            content="",
            thinking=None, reasoning=None, model="t",
            tool_calls=[ToolCallResult(id="tc", function_name="load_reference",
                                       arguments={"name": "genai"})],
        )
        # Always return a tool call — the loop must give up at max_llm_calls.
        mock_tools.return_value = looper
        mock_llm.return_value = LLMResponse(
            content=json.dumps({
                "threat_model": [], "improvement_suggestions": ["partial"],
            }),
            thinking=None, reasoning=None, model="t",
        )
        out = run_quick_analysis(model_pair, "Description.", max_llm_calls=2)
        # Two tool-using turns then forced JSON retry — the cap holds.
        assert mock_tools.call_count == 2
        assert mock_llm.call_count == 1
        assert out.improvement_suggestions == ["partial"]


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


class TestParseThreatModel:
    def test_clean_json(self):
        out = _parse_threat_model('{"threat_model": [], "improvement_suggestions": []}')
        assert out is not None
        assert out.threat_model == []

    def test_markdown_fence(self):
        text = '```json\n{"threat_model": [], "improvement_suggestions": []}\n```'
        out = _parse_threat_model(text)
        assert out is not None

    def test_embedded_in_prose(self):
        text = 'Here is the model:\n{"threat_model": [], "improvement_suggestions": []}\nDone.'
        out = _parse_threat_model(text)
        assert out is not None

    def test_invalid_returns_none(self):
        assert _parse_threat_model("not json at all") is None

    @pytest.mark.parametrize("payload", [
        {"threat_model": ["x"]},
        {"threat_model": [None]},
        {"threat_model": None},
        {"threat_model": {}},
        {"threat_model": [{"Threat Type": "Spoofing", "Scenario": "missing impact"}]},
        {"improvement_suggestions": "not a list"},
        {"improvement_suggestions": [None]},
    ])
    def test_malformed_shapes_return_none_for_retry(self, payload):
        assert _parse_threat_model(json.dumps(payload)) is None


class TestSchemaFailureProtocol:
    @pytest.mark.parametrize("with_reference", [False, True])
    @pytest.mark.parametrize("payload", [
        {"threat_model": ["x"]},
        {"threat_model": None},
        {"improvement_suggestions": [None]},
    ])
    def test_malformed_model_output_retries_with_valid_protocol(
        self, payload, with_reference, model_pair,
    ):
        steps = []
        if with_reference:
            steps.append(call_tools(
                ToolCallResult("reference", "load_reference", {"name": "genai"}),
                tools=QUICK_TOOL_NAMES,
            ))
        steps.extend([
            reply(json.dumps(payload), tools=QUICK_TOOL_NAMES),
            reply(json.dumps({
                "threat_model": [{
                    "Threat Type": "Tampering", "Scenario": "s", "Potential Impact": "i",
                    "CONTROLS": ["IAM-05", "IAM-999"],
                    "MITRE_ATTACK": [{"id": "T1190", "name": "Forged"}, {"id": "T9999"}],
                }],
                "improvement_suggestions": ["fix it"],
            })),
        ])
        with ScriptedLLM(steps) as fake:
            output = run_quick_analysis(model_pair, "Review this application.")
        assert fake.requests[-1].kind == "plain"
        assert output.llm_calls == 2 + int(with_reference)
        assert output.threat_model[0]["CONTROLS"] == ["IAM-05"]
        assert output.threat_model[0]["MITRE_ATTACK"] == [
            {"id": "T1190", "name": "Exploit Public-Facing Application"},
        ]

    def test_malformed_retry_returns_failure_message_without_raising(self, model_pair):
        with ScriptedLLM([
            reply('{"threat_model":["x"]}', tools=QUICK_TOOL_NAMES),
            reply('{"threat_model":[null]}'),
        ]):
            output = run_quick_analysis(model_pair, "Review this application.")
        assert output.threat_model == []
        assert "Failed to parse" in output.improvement_suggestions[0]

    def test_call_limit_retry_keeps_message_protocol(self, model_pair):
        with ScriptedLLM([
            call_tools(
                ToolCallResult("reference", "load_reference", {"name": "genai"}),
                tools=QUICK_TOOL_NAMES,
            ),
            reply('{"threat_model":[],"improvement_suggestions":[]}'),
        ]):
            output = run_quick_analysis(model_pair, "Review this application.", max_llm_calls=1)
        assert output.threat_model == []
        assert output.references_loaded == ["genai"]

    def test_retry_does_not_mutate_original_user_turn(self, llm_config):
        messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "hi"}]
        with ScriptedLLM([reply('{"threat_model":[],"improvement_suggestions":[]}')]):
            _retry_as_json(llm_config, messages)
        assert messages == [{"role": "system", "content": "s"}, {"role": "user", "content": "hi"}]


class TestStripToolArtifacts:
    def test_removes_tool_messages(self):
        msgs = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "", "tool_calls": [{"id": "1"}]},
            {"role": "tool", "tool_call_id": "1", "content": "result"},
            {"role": "user", "content": "next"},
        ]
        cleaned = _strip_tool_artifacts(msgs)
        roles = [m["role"] for m in cleaned]
        assert "tool" not in roles
        assert not any("tool_calls" in m for m in cleaned)


# ---------------------------------------------------------------------------
# Tier routing — main call → architect; retry → worker
# ---------------------------------------------------------------------------


class TestTierRouting:
    @patch("stride_gpt.agent.quick.call_llm")
    @patch("stride_gpt.agent.quick.call_llm_with_tools")
    def test_main_call_uses_architect_retry_uses_worker(
        self, mock_tools, mock_llm, tiered_pair,
    ):
        """The main single-shot judgment hits the architect tier. If JSON
        parse fails, the retry hits the worker tier (same task, stricter
        formatting — no reason to escalate)."""
        mock_tools.return_value = LLMResponse(
            content="not parseable",
            thinking=None, reasoning=None, model="t", tool_calls=None,
        )
        mock_llm.return_value = LLMResponse(
            content=json.dumps({"threat_model": [], "improvement_suggestions": []}),
            thinking=None, reasoning=None, model="t",
        )

        run_quick_analysis(tiered_pair, "Anything.")

        assert mock_tools.call_args.args[0].model_name == tiered_pair.architect.model_name
        assert mock_llm.call_args.args[0].model_name == tiered_pair.worker.model_name

    @patch("stride_gpt.agent.quick.call_llm")
    @patch("stride_gpt.agent.quick.call_llm_with_tools")
    def test_single_tier_uses_worker_everywhere(
        self, mock_tools, mock_llm, model_pair,
    ):
        mock_tools.return_value = LLMResponse(
            content="not parseable",
            thinking=None, reasoning=None, model="t", tool_calls=None,
        )
        mock_llm.return_value = LLMResponse(
            content=json.dumps({"threat_model": [], "improvement_suggestions": []}),
            thinking=None, reasoning=None, model="t",
        )

        run_quick_analysis(model_pair, "Anything.")

        worker_name = model_pair.worker.model_name
        assert mock_tools.call_args.args[0].model_name == worker_name
        assert mock_llm.call_args.args[0].model_name == worker_name


# ---------------------------------------------------------------------------
# _retry_as_json — forced-JSON retry fallback
# ---------------------------------------------------------------------------


class TestRetryAsJson:
    @patch("stride_gpt.agent.quick.call_llm")
    def test_retry_success_returns_parsed_model(self, mock_llm, llm_config):
        mock_llm.return_value = LLMResponse(
            content=json.dumps({
                "threat_model": [{"Threat Type": "Spoofing", "Scenario": "s", "Potential Impact": "i"}],
                "improvement_suggestions": ["x"],
            }),
            thinking=None, reasoning=None, model="t",
        )
        out = _retry_as_json(llm_config, [{"role": "user", "content": "hi"}])
        assert len(out.threat_model) == 1
        assert out.improvement_suggestions == ["x"]

    @patch("stride_gpt.agent.quick.call_llm")
    def test_double_failure_returns_empty_with_message(self, mock_llm, llm_config):
        """When even the forced-JSON retry can't be parsed, the user gets an
        empty threat model carrying a specific 'failed to parse' note rather
        than an exception."""
        mock_llm.return_value = LLMResponse(
            content="still not json {{{",
            thinking=None, reasoning=None, model="t",
        )
        out = _retry_as_json(llm_config, [{"role": "user", "content": "hi"}])
        assert out.threat_model == []
        assert out.improvement_suggestions == ["Failed to parse model response as JSON."]


class TestMalformedToolArguments:
    @patch("stride_gpt.agent.quick.call_llm_with_tools")
    def test_parse_error_returned_as_tool_result(self, mock_tools, model_pair):
        bad = ToolCallResult(
            id="bad", function_name="load_reference", arguments={},
            parse_error="arguments were not valid JSON (Unterminated string)",
        )
        turn1 = LLMResponse(content="", model="t", tool_calls=[bad])
        mock_tools.side_effect = [turn1, _final_response()]

        out = run_quick_analysis(model_pair, "Any description.")

        msgs = mock_tools.call_args_list[1].args[1]
        tool_msgs = [m for m in msgs if m.get("role") == "tool"]
        assert tool_msgs[0]["tool_call_id"] == "bad"
        assert tool_msgs[0]["content"].startswith("Error: arguments were not valid JSON")
        assert out.tool_calls == 1
