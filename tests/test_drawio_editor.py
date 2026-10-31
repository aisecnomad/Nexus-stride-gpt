"""Exercise operator URL validation and browser message-origin enforcement."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from apps.web.components.drawio_editor import _resolve_drawio_url


@pytest.mark.parametrize("origin", ["https://embed.diagrams.net", "https://drawio.internal.example:8443/"])
def test_https_editor_origins_remain_supported(monkeypatch, origin):
    monkeypatch.setenv("STRIDE_GPT_DRAWIO_URL", origin)
    assert _resolve_drawio_url().startswith(origin.rstrip("/") + "/?embed=1&")


@pytest.mark.parametrize("origin", [
    "http://drawio.internal", "javascript:alert(1)", "data:text/html,editor",
    "https://user:password@editor.example", "https://editor.example/path",
    "https://editor.example?query=value", "https://editor.example#fragment",
    "https://editor.example:bad", "https://",
])
def test_unsafe_or_ambiguous_editor_url_is_rejected(monkeypatch, origin):
    monkeypatch.setenv("STRIDE_GPT_DRAWIO_URL", origin)
    with pytest.raises(ValueError):
        _resolve_drawio_url()


@pytest.mark.skipif(shutil.which("node") is None, reason="Browser message harness needs Node")
def test_iframe_messages_require_exact_window_and_origin():
    frontend = Path(__file__).parents[1] / "apps/web/components/drawio_editor/frontend/index.html"
    # Extract the trusted fixture's inline script; this is not an HTML sanitizer.
    match = re.search(r"<script>(.*?)</script>", frontend.read_text(), re.DOTALL | re.IGNORECASE)
    assert match is not None
    script = match.group(1)
    harness = r'''
const fs = require("fs");
const vm = require("vm");
const assert = require("assert");
const source = fs.readFileSync(0, "utf8");
function boot() {
  let handler;
  const sent = [];
  const parent = {postMessage() {}};
  const child = {postMessage(msg, origin) {sent.push({msg, origin});}};
  const frame = {contentWindow: child, src: ""};
  const elements = {"drawio-frame": frame};
  const context = {
    URL,
    window: {parent, addEventListener(event, callback) {handler = callback;}},
    document: {getElementById(id) {
      return elements[id] ||= {addEventListener() {}, textContent: ""};
    }}
  };
  vm.runInNewContext(source, context);
  return {context, sent, parent, child, frame, send(evt) {handler(evt);}};
}
const app = boot();
const render = {type: "streamlit:render", args: {drawio_url: "https://embed.diagrams.net/?embed=1", xml: ""}};
app.send({source: {}, data: render});
assert.strictEqual(app.frame.src, "");
app.send({source: app.parent, data: render});
assert.ok(app.frame.src.startsWith("https://embed.diagrams.net/"));
app.send({source: {}, origin: "https://embed.diagrams.net", data: '{"event":"init"}'});
app.send({source: app.child, origin: "https://attacker.invalid", data: '{"event":"init"}'});
assert.strictEqual(app.sent.length, 0);
app.send({source: app.child, origin: "https://embed.diagrams.net", data: '{"event":"init"}'});
assert.strictEqual(app.sent.length, 1);
assert.strictEqual(app.sent[0].origin, "https://embed.diagrams.net");
const invalid = boot();
invalid.send({source: invalid.parent, data: {type:"streamlit:render",args:{drawio_url:"javascript:alert(1)"}}});
invalid.send({source: invalid.child, origin:"null", data:'{"event":"init"}'});
assert.strictEqual(invalid.frame.src, "");
assert.strictEqual(invalid.sent.length, 0);
'''
    result = subprocess.run(
        [shutil.which("node"), "-e", harness], input=script, text=True,
        capture_output=True, timeout=10, check=False,
    )
    assert result.returncode == 0, result.stderr


def test_oversized_component_result_is_not_stored(monkeypatch):
    import apps.web.components.drawio_editor as editor

    monkeypatch.setattr(editor, "MAX_DRAWIO_CHARS", 3)
    monkeypatch.setattr(editor, "_component_func", lambda **_kwargs: {"action": "save", "xml": "xxxx"})
    result = editor.drawio_editor_component()
    assert result["action"] == "error"
    assert "xml" not in result
