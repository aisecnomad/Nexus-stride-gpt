"""Resolve server credentials without exposing them in Streamlit widgets.

Session state holds only credentials entered by the current user. Operator
credentials remain in the server environment and are resolved only when making
a request. Shared by the sidebar, the Data Flow Diagram tab, and the guided-draft
resolver in ``main.py``, and cross-checked against the provider registry by
``tests/test_provider_keys.py`` so a newly added provider can't silently miss a
mapping.

LM Studio is intentionally absent: it authenticates via a custom endpoint
(``api_base``) plus an optional key, so it is handled separately by callers.
"""

from __future__ import annotations

import os
from collections.abc import Mapping

from stride_gpt.models import PROVIDERS

# provider_key (LLMConfig.provider) -> user-supplied credential in session state.
PROVIDER_API_KEY_STATE: dict[str, str] = {
    "OpenAI API": "openai_api_key",
    "Anthropic API": "anthropic_api_key",
    "Google AI API": "google_api_key",
    "Mistral API": "mistral_api_key",
    "Groq API": "groq_api_key",
    "DeepSeek API": "deepseek_api_key",
    "OpenRouter API": "openrouter_api_key",
}

_PROVIDER_ENV = {
    info.provider_key: info.env_var for info in PROVIDERS.values() if info.env_var
}


def has_server_api_key(provider: str) -> bool:
    """Safe UI indicator; never return a server credential to a widget."""
    env_var = _PROVIDER_ENV.get(provider)
    return bool(env_var and os.environ.get(env_var))


def resolve_provider_api_key(provider: str, user_state: Mapping[str, str]) -> str:
    """Prefer a user override, otherwise use the operator's server credential."""
    state_key = PROVIDER_API_KEY_STATE.get(provider)
    if state_key and user_state.get(state_key):
        return user_state[state_key]
    env_var = _PROVIDER_ENV.get(provider)
    return os.environ.get(env_var, "") if env_var else ""


def resolve_github_api_key(user_state: Mapping[str, str]) -> str:
    """Use the session token, unless shared server-token access is opted in.

    A deployment-wide token can access private repositories irrespective of
    the current user's GitHub permissions. Explicit opt-in is only suitable
    when all users of the deployment share that token's trust boundary.
    """
    user_token = user_state.get("github_api_key", "")
    if user_token:
        return user_token
    if os.environ.get("STRIDE_GPT_ALLOW_SHARED_GITHUB_TOKEN", "").strip().lower() == "true":
        return os.environ.get("GITHUB_API_KEY", "")
    return ""


def has_shared_github_api_key() -> bool:
    """Whether the operator has explicitly enabled a shared GitHub token."""
    return bool(resolve_github_api_key({}))
