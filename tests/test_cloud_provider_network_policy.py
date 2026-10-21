"""Direct cloud-provider calls must enforce the shared network/data policy."""

from unittest.mock import Mock

import pytest

from llm.cloud.anthropic import AnthropicProvider
from llm.cloud.gemini import GeminiProvider
from llm.cloud.mistral import MistralProvider
from llm.cloud.openai_provider import OpenAIProvider
from llm.cloud.openrouter import OpenRouterProvider
from policy.network_mode import NetworkAccessDisabledError


@pytest.mark.parametrize(
    "factory",
    [
        lambda: GeminiProvider(api_key="test-key"),
        lambda: OpenRouterProvider(api_key="test-key"),
        lambda: AnthropicProvider(api_key="test-key"),
        lambda: MistralProvider(api_key="test-key"),
        lambda: OpenAIProvider(api_key="test-key", client=Mock()),
    ],
)
def test_direct_cloud_provider_rejects_offline_mode_before_network(factory, monkeypatch):
    monkeypatch.setenv("FINAI_NETWORK_MODE", "offline")
    monkeypatch.delenv("FINAI_DATA_SENSITIVITY", raising=False)
    monkeypatch.delenv("FINAI_ALLOWED_PROVIDERS", raising=False)
    provider = factory()

    with pytest.raises(NetworkAccessDisabledError, match="offline mode"):
        provider.generate(
            user_text="Explain an EMI.",
            intent="EMI_QUERY",
            verified_result={},
            source="test",
        )


@pytest.mark.parametrize(
    "factory",
    [
        lambda: GeminiProvider(api_key="test-key"),
        lambda: OpenRouterProvider(api_key="test-key"),
        lambda: AnthropicProvider(api_key="test-key"),
        lambda: MistralProvider(api_key="test-key"),
        lambda: OpenAIProvider(api_key="test-key", client=Mock()),
    ],
)
def test_direct_cloud_provider_rejects_restricted_data(factory, monkeypatch):
    monkeypatch.setenv("FINAI_NETWORK_MODE", "online")
    monkeypatch.setenv("FINAI_DATA_SENSITIVITY", "restricted")
    monkeypatch.delenv("FINAI_ALLOWED_PROVIDERS", raising=False)
    provider = factory()

    with pytest.raises(NetworkAccessDisabledError, match="restricted data"):
        provider.generate(
            user_text="Explain an EMI.",
            intent="EMI_QUERY",
            verified_result={},
            source="test",
        )


def test_direct_cloud_provider_obeys_provider_allow_list(monkeypatch):
    monkeypatch.setenv("FINAI_NETWORK_MODE", "online")
    monkeypatch.setenv("FINAI_DATA_SENSITIVITY", "standard")
    monkeypatch.setenv("FINAI_ALLOWED_PROVIDERS", "openai")
    provider = GeminiProvider(api_key="test-key")

    with pytest.raises(NetworkAccessDisabledError, match="allow-list"):
        provider.generate(
            user_text="Explain an EMI.",
            intent="EMI_QUERY",
            verified_result={},
            source="test",
        )
