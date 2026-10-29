"""Tripwire tests for the provider -> session-state API-key mapping.

The web UI maps user-supplied credential overrides with
``apps/web/provider_keys.PROVIDER_API_KEY_STATE``, falling back to the server
environment only at request time. If a provider is added to the registry in
``stride_gpt.models`` but not to that map, its guided draft / key lookup would
silently fall back or fail. These tests fail if the two ever drift.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# apps/web isn't a package on the default path; add it so we can import the map.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "web"))

from provider_keys import (
    PROVIDER_API_KEY_STATE,
    has_server_api_key,
    resolve_github_api_key,
    resolve_provider_api_key,
)

from stride_gpt.models import PROVIDERS


def test_every_api_key_provider_is_mapped():
    """Every registry provider that authenticates with an API key is mapped."""
    for info in PROVIDERS.values():
        # LM Studio authenticates via a custom endpoint (api_base) plus an
        # optional key, and is handled separately by callers.
        if info.needs_api_base or not info.needs_api_key:
            continue
        assert info.provider_key in PROVIDER_API_KEY_STATE, (
            f"Provider {info.provider_key!r} is in stride_gpt.models.PROVIDERS but "
            f"missing from PROVIDER_API_KEY_STATE (apps/web/provider_keys.py). "
            f"Add its session-state key."
        )


def test_no_stale_mappings():
    """Every mapped provider still exists in the registry."""
    valid_provider_keys = {info.provider_key for info in PROVIDERS.values()}
    for provider_key in PROVIDER_API_KEY_STATE:
        assert provider_key in valid_provider_keys, (
            f"PROVIDER_API_KEY_STATE maps {provider_key!r}, which is not a known "
            f"provider in stride_gpt.models.PROVIDERS."
        )


@pytest.mark.parametrize(
    "provider,state_key",
    list(PROVIDER_API_KEY_STATE.items()),
)
def test_credentials_resolve_without_copying_server_keys_to_user_state(
    monkeypatch, provider, state_key
):
    info = next(info for info in PROVIDERS.values() if info.provider_key == provider)
    monkeypatch.setenv(info.env_var, "fake-server-key")
    monkeypatch.setenv("GITHUB_API_KEY", "fake-server-github-key")
    user_state = {}
    assert has_server_api_key(provider)
    assert resolve_provider_api_key(provider, user_state) == "fake-server-key"
    assert resolve_github_api_key(user_state) == "fake-server-github-key"
    assert user_state == {}
    user_state.update({state_key: "fake-user-key", "github_api_key": "fake-user-github-key"})
    assert resolve_provider_api_key(provider, user_state) == "fake-user-key"
    assert resolve_github_api_key(user_state) == "fake-user-github-key"

    # Environment rotation applies on the next request without copying either
    # credential into session state; clearing an override restores that fallback.
    monkeypatch.setenv(info.env_var, "fake-rotated-server-key")
    assert resolve_provider_api_key(provider, user_state) == "fake-user-key"
    user_state[state_key] = ""
    assert resolve_provider_api_key(provider, user_state) == "fake-rotated-server-key"
    assert user_state[state_key] == ""
    monkeypatch.delenv(info.env_var)
    assert not has_server_api_key(provider)
    assert resolve_provider_api_key(provider, user_state) == ""


def test_unknown_provider_has_no_credential_fallback():
    assert not has_server_api_key("unknown")
    assert resolve_provider_api_key("unknown", {}) == ""
