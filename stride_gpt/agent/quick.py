"""Quick single-shot threat model — agent loop without filesystem tools.

The user provides an application description (free-form text). The agent
reads it, decides which OWASP / insider-threat reference cards apply, calls
``load_reference`` for each, then emits a STRIDE threat model as JSON.

This is the same progressive-disclosure pattern as the codebase-driven
``/analyze`` path, but slimmed down: no codebase, no filesystem tools, no
planner / per-subsystem split / synthesis pass. Just description in, threat
model out, with the agent picking the right reference lenses along the way.
"""

from __future__ import annotations

import json

from stride_gpt.agent.tools import AGENT_TOOLS
from stride_gpt.core.controls import keep_known_controls
from stride_gpt.core.json_extract import extract_json_object
from stride_gpt.core.llm import call_llm, call_llm_with_tools
from stride_gpt.core.prompts import quick_base_prompt
from stride_gpt.core.prompts.variants import list_references, load_reference
from stride_gpt.core.schemas import LLMConfig, ModelPair, ThreatModelOutput, ToolCallResult
from stride_gpt.core.threat_model import validate_threat_model_data

# Quick analysis only gets the reference-card tools — no filesystem since
# there's no codebase to explore.
QUICK_TOOL_NAMES = frozenset({"load_reference", "list_references"})
QUICK_TOOLS = [
    t for t in AGENT_TOOLS if t["function"]["name"] in QUICK_TOOL_NAMES
]


def _execute_quick_tool(tool_call: ToolCallResult, loaded_refs: set[str]) -> str:
    """Enforce the reference-only capability boundary on model output.

    Advertising a subset of tools to a provider does not authorize execution:
    a provider or a local model can still return an unadvertised function name.
    This dispatcher has no analysis root or access to the filesystem executor.
    Every refused call still receives a tool result to preserve chat protocol.
    """
    if tool_call.function_name not in QUICK_TOOL_NAMES:
        return (
            f"Error: tool '{tool_call.function_name}' is not available in quick analysis. "
            "Only list_references and load_reference are allowed."
        )
    if tool_call.parse_error:
        return (
            f"Error: {tool_call.parse_error}. "
            "Re-issue the call with a valid JSON object."
        )
    try:
        if tool_call.function_name == "list_references":
            return json.dumps(list_references(), indent=2)
        name = tool_call.arguments["name"]
        result = load_reference(name)
    except Exception as e:
        return f"Error executing {tool_call.function_name}: {e}"
    if not result.startswith("Error:"):
        loaded_refs.add(name)
    return result


def run_quick_analysis(
    models: ModelPair,
    app_description: str,
    *,
    hint: str | None = None,
    max_llm_calls: int = 4,
) -> ThreatModelOutput:
    """Produce a STRIDE threat model from an application description.

    Args:
        models: Worker + optional architect LLM configuration. The main
            single-shot threat-model judgment uses the architect tier
            (reasoning-heavy); the JSON-coercion retry uses the worker.
        app_description: Free-form description of the application to model.
        hint: Optional declared application type (``"Web application"`` /
            ``"Generative AI application"`` / ``"Agentic AI application"``).
            Passed to the model as a hint in the user message — the model
            still decides which reference cards to load.
        max_llm_calls: Hard cap on LLM calls (including any tool-handling
            turns and a final retry). 4 is typically plenty: one turn to
            load cards, one to emit JSON, plus headroom.

    Returns:
        ``ThreatModelOutput`` with ``threat_model`` (list of threat dicts)
        and ``improvement_suggestions`` (list of strings).
    """
    user_content = _build_user_content(app_description, hint)
    messages: list[dict] = [
        {"role": "system", "content": quick_base_prompt()},
        {"role": "user", "content": user_content},
    ]

    llm_calls = 0
    tool_calls = 0
    tools_used: dict[str, int] = {}
    # Cache load_reference results so the model doesn't waste turns calling
    # the same card twice. Card content is idempotent so the cache is safe.
    tool_cache: dict[str, str] = {}
    # Names the agent loads via the ``load_reference`` tool. Surfaced on the
    # returned ``ThreatModelOutput`` so the run manifest can record which
    # cards actually shaped the output.
    loaded_refs: set[str] = set()

    while llm_calls < max_llm_calls:
        response = call_llm_with_tools(models.for_architect(), messages, QUICK_TOOLS)
        llm_calls += 1

        if response.tool_calls:
            messages.append({
                "role": "assistant",
                "content": response.content or "",
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function_name,
                                  "arguments": json.dumps(tc.arguments)}}
                    for tc in response.tool_calls
                ],
            })
            for tc in response.tool_calls:
                key = tc.function_name + ":" + json.dumps(tc.arguments, sort_keys=True)
                if not tc.parse_error and key in tool_cache:
                    result = (
                        "You already loaded this reference card. Refer to the "
                        "earlier tool response instead of requesting it again."
                    )
                else:
                    result = _execute_quick_tool(tc, loaded_refs)
                    if not tc.parse_error and not result.startswith("Error:"):
                        tool_cache[key] = result
                tool_calls += 1
                tools_used[tc.function_name] = tools_used.get(tc.function_name, 0) + 1
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.function_name,
                    "content": result,
                })
            continue

        # No tool calls — model produced (or attempted) the final JSON.
        parsed = _parse_threat_model(response.content)
        if parsed is None:
            # JSON parse failed — one retry with forced JSON mode.
            parsed = _retry_as_json(models.worker, messages)
            llm_calls += 1
        return _attach_counts(parsed, llm_calls, tool_calls, tools_used, loaded_refs)

    # Hit the call cap before getting a final JSON — coerce one last attempt.
    messages.append({
        "role": "user",
        "content": (
            "You've reached the analysis call limit. Produce your STRIDE threat "
            "model now as JSON in the schema specified, based on what you have. "
            "Do not call any more tools."
        ),
    })
    parsed = _retry_as_json(models.worker, messages)
    llm_calls += 1
    return _attach_counts(parsed, llm_calls, tool_calls, tools_used, loaded_refs)


def _attach_counts(
    output: ThreatModelOutput,
    llm_calls: int,
    tool_calls: int,
    tools_used: dict[str, int],
    loaded_refs: set[str],
) -> ThreatModelOutput:
    output.llm_calls = llm_calls
    output.tool_calls = tool_calls
    output.tools_used = tools_used
    output.references_loaded = sorted(loaded_refs)
    return output


def _build_user_content(app_description: str, hint: str | None) -> str:
    if hint:
        return (
            f"The user has indicated this is a **{hint}**. Treat that as a "
            f"strong hint about which reference cards apply, but verify it "
            f"against the description below before loading cards.\n\n"
            f"## Application description\n\n{app_description}"
        )
    return f"## Application description\n\n{app_description}"


def _parse_threat_model(content: str) -> ThreatModelOutput | None:
    """Extract a ThreatModelOutput from model text. Returns None on failure."""
    data = extract_json_object(content)
    if data is None:
        return None
    try:
        output = validate_threat_model_data(data)
    except ValueError:
        return None
    # Validate before operating on threat dictionaries. The saved report is
    # what downstream tools import; invented control IDs must not reach it.
    for threat in output.threat_model:
        keep_known_controls(threat)
    return output


def _retry_as_json(config: LLMConfig, messages: list[dict]) -> ThreatModelOutput:
    """Retry with forced JSON mode after a parse failure.

    Strips tool-call artefacts so the plain-LLM call doesn't choke on
    function-calling metadata.
    """
    clean = _strip_tool_artifacts(messages)
    instruction = (
        "Respond with ONLY a valid JSON object matching the schema in your "
        "instructions. No prose, no markdown fences, no commentary."
    )
    if clean and clean[-1].get("role") == "user":
        # A first-turn parse failure or call-limit coercion already ends in
        # a user turn. Keep a strict provider's alternating-message protocol
        # and do not modify the caller's original message dictionary.
        clean[-1] = {**clean[-1], "content": f"{clean[-1].get('content', '')}\n\n{instruction}"}
    else:
        clean.append({"role": "user", "content": instruction})
    json_config = config.model_copy(update={"response_format": "json"})
    response = call_llm(json_config, clean)
    parsed = _parse_threat_model(response.content)
    if parsed is not None:
        return parsed
    return ThreatModelOutput(
        threat_model=[],
        improvement_suggestions=["Failed to parse model response as JSON."],
    )


def _strip_tool_artifacts(messages: list[dict]) -> list[dict]:
    """Drop tool messages and tool_calls metadata so a plain LLM call works."""
    cleaned: list[dict] = []
    for msg in messages:
        if msg.get("role") == "tool":
            continue
        if "tool_calls" in msg:
            cleaned.append({"role": msg["role"], "content": msg.get("content", "")})
        else:
            cleaned.append(msg)
    return cleaned
