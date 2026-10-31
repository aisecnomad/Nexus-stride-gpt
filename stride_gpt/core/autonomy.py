"""ShadowScan-compatible autonomy vocabulary shared by CLI and web guidance.

Level numbers alone are not interchangeable with older STRIDE-GPT reports or
other frameworks. This module defines vocabulary, not a code classifier.
"""

from __future__ import annotations

from typing import Any

AUTONOMY_TAXONOMY = "shadowscan.autonomy/v1"
AUTONOMY_SOURCE = (
    "https://github.com/aisecnomad/Nexus-ShadowScan/blob/main/docs/concepts/autonomy.md"
)

# Keep insertion order: it is also the display and tool-schema order.
AUTONOMY_LABELS: dict[str, str] = {
    "L0": "Chatbot",
    "L1": "Copilot",
    "L2": "Supervised",
    "L3": "Semi-Autonomous / Agentic Workflow",
    "L4": "High Autonomy",
    "L5": "Fully Autonomous",
}
AUTONOMY_LEVELS = list(AUTONOMY_LABELS)
AUTONOMY_DESCRIPTIONS: dict[str, str] = {
    "L0": "Answers only; no tools or actions. A person starts every exchange.",
    "L1": (
        "Assists a person in their session: drafts, suggests or retrieves with "
        "read-only tools. The person performs or confirms every action."
    ),
    "L2": (
        "A person starts the run and approves each side-effecting tool action "
        "before execution."
    ),
    "L3": (
        "Runs a bounded multi-step workflow or model-driven loop; approval is "
        "at checkpoints, not per action. May be event-triggered."
    ),
    "L4": (
        "The model plans and acts in a loop with write or execution capabilities "
        "and no per-action approval. People supervise by exception."
    ),
    "L5": (
        "Starts itself through an event, schedule or another agent, acts with "
        "write, execute or delegated capabilities and no approval gates. "
        "People only monitor."
    ),
}
AUTONOMY_SCHEMA_DESCRIPTION = (
    "Evidence-supported level on the ShadowScan scale: "
    + "; ".join(f"{level} {label}" for level, label in AUTONOMY_LABELS.items())
    + ". Use the insider_threat card for approval and initiation criteria; "
    "omit when these are unknown. Tools or credentials alone do not establish a level."
)


def autonomy_scale_markdown() -> str:
    """Render the scale for user guidance without duplicating UI labels."""
    rows = ["| Level | Name | Behaviour and oversight |", "|---|---|---|"]
    rows.extend(
        f"| {level} | {label} | {AUTONOMY_DESCRIPTIONS[level]} |"
        for level, label in AUTONOMY_LABELS.items()
    )
    return "\n".join(rows)


def normalize_generated_autonomy(threat: dict[str, Any]) -> dict[str, Any]:
    """Validate vocabulary and stamp taxonomy at model-output ingestion only.

    This marker identifies the scale used, not whether the model's assessment
    is supported by evidence. It must never be applied on report load/render:
    old reports used different meanings for the same numeric strings.
    """
    result = dict(threat)
    # The model cannot choose the vocabulary provenance the application asserts.
    result.pop("autonomy_taxonomy", None)
    level = result.get("autonomy_level")
    if isinstance(level, str) and level in AUTONOMY_LABELS:
        result["autonomy_taxonomy"] = AUTONOMY_TAXONOMY
    else:
        # Unknown and malformed values stay unclassified, never coerced to L0.
        result.pop("autonomy_level", None)
    return result
