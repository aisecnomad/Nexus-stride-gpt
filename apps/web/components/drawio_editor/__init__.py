"""Streamlit custom component that embeds the diagrams.net editor.

The component returns a dict  {action: "save"|"close", xml: str} (or an error dict)
when the user saves or cancels, and None while the editor is idle.
"""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import streamlit.components.v1 as components

from stride_gpt.core.drawio_parser import MAX_DRAWIO_CHARS

_FRONTEND = str(Path(__file__).parent / "frontend")
_component_func = components.declare_component("drawio_editor", path=_FRONTEND)

_DEFAULT_DRAWIO_HOST = "https://embed.diagrams.net"
# Query params the JSON embed protocol this component speaks requires.
_EMBED_PARAMS = "?embed=1&proto=json&spin=1&ui=min&dark=0&noSaveBtn=0&saveAndExit=0"


def _resolve_drawio_url() -> str:
    """Full draw.io editor URL used by the iframe.

    Defaults to the public diagrams.net embed. Set ``STRIDE_GPT_DRAWIO_URL`` to
    the scheme+host of a self-hosted draw.io (e.g.
    ``https://drawio.internal.example.com``) for air-gapped/enterprise
    deployments; the embed query params are appended automatically.
    """
    host = os.environ.get("STRIDE_GPT_DRAWIO_URL", _DEFAULT_DRAWIO_HOST).strip().rstrip("/")
    parsed = urlsplit(host)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username is not None
            or parsed.password is not None or parsed.query or parsed.fragment
            or parsed.path not in ("", "/")):
        raise ValueError("STRIDE_GPT_DRAWIO_URL must be an HTTPS origin without credentials or a path.")
    # Accessing port also rejects malformed ports instead of deferring to the browser.
    _ = parsed.port
    return urlunsplit(("https", parsed.netloc, "/", _EMBED_PARAMS[1:], ""))


def drawio_editor_component(xml: str = "", key: str | None = None) -> dict | None:
    """Render the embedded draw.io editor.

    Args:
        xml:  Optional draw.io XML to pre-load. Pass "" for a blank canvas.
        key:  Streamlit widget key for state isolation.

    Returns:
        None while the editor is open and the user hasn't acted.
        {"action": "save", "xml": "<mxGraphModel...>"}  on save.
        {"action": "close", "xml": ""}  on cancel.
        {"action": "error", "error": "..."} for an invalid or oversized save.
    """
    result = _component_func(
        xml=xml, drawio_url=_resolve_drawio_url(), key=key, default=None
    )
    if not isinstance(result, dict):
        return None
    if result.get("action") == "close":
        return {"action": "close", "xml": ""}
    if result.get("action") != "save":
        return None
    diagram = result.get("xml")
    if not isinstance(diagram, str) or len(diagram) > MAX_DRAWIO_CHARS:
        return {"action": "error", "error": "The diagram is invalid or exceeds one million characters."}
    return {"action": "save", "xml": diagram}
