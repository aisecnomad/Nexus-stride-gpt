"""Core threat model generation logic. Zero Streamlit imports."""

from __future__ import annotations

import json
import re

from stride_gpt.core.llm import call_llm, call_llm_with_image
from stride_gpt.core.markdown_safety import sanitize_markdown
from stride_gpt.core.mitre import normalize_threat_mitre
from stride_gpt.core.prompts import create_image_analysis_prompt, create_reasoning_system_prompt
from stride_gpt.core.schemas import LLMConfig, LLMResponse, ThreatModelOutput
from stride_gpt.models import model_uses_completion_tokens

THREAT_MODEL_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "threat_model": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "Threat Type": {"type": "string"},
                    "Scenario": {"type": "string"},
                    "Potential Impact": {"type": "string"},
                    "OWASP_LLM": {"type": ["string", "null"]},
                    "OWASP_ASI": {"type": ["string", "null"]},
                    "INSIDER_CATEGORY": {"type": ["string", "null"]},
                    "CONTROLS": {"type": ["array", "null"], "items": {"type": "string"}},
                },
                "required": ["Threat Type", "Scenario", "Potential Impact"],
            },
        },
        "improvement_suggestions": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["threat_model", "improvement_suggestions"],
}


def generate_threat_model(config: LLMConfig, prompt: str) -> tuple[ThreatModelOutput, LLMResponse]:
    """Generate a threat model using any supported LLM provider."""
    system_prompt = _get_system_prompt(config)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    # LM Studio doesn't support json_object mode — without an explicit schema it
    # gets no structured-output enforcement at all and frequently emits prose
    # that fails JSON parsing. Hand it the schema; other providers keep the
    # existing json_object path to avoid regressions in callers that depend on it.
    if config.provider == "LM Studio Server":
        json_config = config.model_copy(update={"response_format": THREAT_MODEL_SCHEMA})
    else:
        json_config = config.model_copy(update={"response_format": "json"})
    response = call_llm(json_config, messages)
    parsed = _parse_threat_model_response(response.content)
    return parsed, response


def analyze_image(
    config: LLMConfig,
    base64_image: str,
    media_type: str = "image/jpeg",
) -> LLMResponse:
    """Analyze an architecture diagram image."""
    prompt = create_image_analysis_prompt()
    return call_llm_with_image(config, prompt, base64_image, media_type)


def json_to_markdown(threat_model, improvement_suggestions):
    """Render a single-shot threat model as markdown.

    Optional columns (OWASP LLM, OWASP ASI, Insider Category, MITRE ATT&CK,
    Controls) appear only when at least one threat carries a value for them —
    same conditional shape as the agent's per-subsystem renderer, via shared
    helpers. Threats that carry controls also get the controls and
    compliance mapping section.
    """
    from stride_gpt.core.report_utils import (
        compliance_section_lines,
        detect_extra_columns,
        threat_table_header,
        threat_table_row,
    )

    cols = detect_extra_columns(threat_model)
    header, separator = threat_table_header(*cols)

    lines = ["## Threat Model", "", header, separator]
    lines.extend(
        threat_table_row(threat, *cols)
        for threat in threat_model
    )

    compliance = compliance_section_lines(threat_model)
    if compliance:
        lines.append("")
        lines.extend(compliance)

    lines.extend(["", "", "## Improvement Suggestions", ""])
    lines.extend(f"- {suggestion}" for suggestion in improvement_suggestions)
    lines.append("")

    return sanitize_markdown("\n".join(lines))


def _get_system_prompt(config: LLMConfig) -> str:
    if model_uses_completion_tokens(config.model_name):
        return create_reasoning_system_prompt(
            task_description="Analyze the provided application description and generate a comprehensive threat model using the STRIDE methodology.",
            approach_description="""1. Carefully read and understand the application description
2. For each component and data flow:
   - Identify potential Spoofing threats
   - Identify potential Tampering threats
   - Identify potential Repudiation threats
   - Identify potential Information Disclosure threats
   - Identify potential Denial of Service threats
   - Identify potential Elevation of Privilege threats
3. For each identified threat:
   - Describe the specific scenario
   - Analyze the potential impact
4. Generate improvement suggestions based on identified threats
5. Format the output as a JSON object with 'threat_model' and 'improvement_suggestions' arrays""",
        )
    return "You are a helpful assistant designed to output JSON."


def _parse_threat_model_response(content: str) -> ThreatModelOutput:
    cleaned = _clean_json_content(content)
    try:
        data = json.loads(cleaned)
        return validate_threat_model_data(data)
    except ValueError as e:
        raw = (content or "").strip()
        snippet = raw[:500].replace("\n", " ").replace("|", "\\|") or "(empty response)"
        truncated = " ..." if len(raw) > 500 else ""
        return ThreatModelOutput(
            threat_model=[
                {
                    "Threat Type": "Error",
                    "Scenario": "Failed to parse LLM response as JSON",
                    "Potential Impact": "Unable to generate threat model",
                }
            ],
            improvement_suggestions=[
                (
                    f"JSON parse error: {e.msg} (line {e.lineno}, col {e.colno})"
                    if isinstance(e, json.JSONDecodeError)
                    else f"JSON schema error: {e}"
                ),
                f"Raw LLM response (first 500 chars): {snippet}{truncated}",
                "Try again — local models sometimes need a second attempt to produce valid JSON",
            ],
        )


def validate_threat_model_data(data: object) -> ThreatModelOutput:
    """Validate the output shape before it reaches renderers and exports.

    Shared by the web single-shot and CLI quick parsers. Empty/missing
    arrays retain the older response contract. A malformed
    array or threat is an explicit generation failure, never an apparently
    successful empty report or a renderer exception.
    """
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")
    threats = data.get("threat_model", [])
    suggestions = data.get("improvement_suggestions", [])
    if not isinstance(threats, list):
        raise ValueError("threat_model must be an array of objects")
    if not isinstance(suggestions, list) or any(not isinstance(s, str) for s in suggestions):
        raise ValueError("improvement_suggestions must be an array of strings")
    for index, threat in enumerate(threats):
        if not isinstance(threat, dict):
            raise ValueError(f"threat_model[{index}] must be an object")
        for key in ("Threat Type", "Scenario", "Potential Impact"):
            if not isinstance(threat.get(key), str):
                raise ValueError(f"threat_model[{index}].{key} must be a string")
    return ThreatModelOutput(
        threat_model=[normalize_threat_mitre(threat) for threat in threats],
        improvement_suggestions=suggestions,
    )


def _clean_json_content(content: str) -> str:
    """Recover common JSON wrappers without rewriting quoted source text.

    Valid JSON is returned unchanged. Only a complete outer Markdown fence
    is unwrapped; comment and trailing-comma recovery operates outside JSON
    strings, preserving URLs, escaped quotes and code examples verbatim.
    """
    content = content.strip()
    try:
        json.loads(content)
        return content
    except json.JSONDecodeError:
        pass
    fence = re.fullmatch(r"```(?:json)?[ \t]*\r?\n(.*?)\r?\n[ \t]*```", content, re.DOTALL | re.IGNORECASE)
    if fence:
        content = fence[1].strip()

    # Strip line comments, retaining their newline so adjacent JSON tokens
    # cannot accidentally be concatenated into a different valid value.
    cleaned: list[str] = []
    in_string = False
    escaped = False
    index = 0
    while index < len(content):
        char = content[index]
        if not in_string and content.startswith("//", index):
            newline = content.find("\n", index)
            index = len(content) if newline < 0 else newline
            continue
        cleaned.append(char)
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        index += 1

    content = "".join(cleaned)
    cleaned = []
    in_string = False
    escaped = False
    for index, char in enumerate(content):
        if not in_string and char == ",":
            next_index = index + 1
            while next_index < len(content) and content[next_index].isspace():
                next_index += 1
            if next_index < len(content) and content[next_index] in "]}":
                continue
        cleaned.append(char)
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
    return "".join(cleaned).strip()
