"""Tests for NVIDIA API client."""
import pytest
from promptforge.integrations.nvidia_api import MODEL_REGISTRY, NVIDIAAPIClient


class TestModelRegistry:
    def test_glm52_registered(self):
        assert "glm-5.2" in MODEL_REGISTRY
        assert MODEL_REGISTRY["glm-5.2"]["id"] == "z-ai/glm-5.2"

    def test_llama8b_registered(self):
        assert "llama-8b" in MODEL_REGISTRY
        assert MODEL_REGISTRY["llama-8b"]["id"] == "meta/llama-3.1-8b-instruct"

    def test_all_models_have_required_fields(self):
        for alias, config in MODEL_REGISTRY.items():
            assert "id" in config, f"{alias} missing id"
            assert "max_tokens" in config, f"{alias} missing max_tokens"


class TestNVIDIAAPIClient:
    def test_requires_api_key(self):
        with pytest.raises(ValueError, match="API key is required"):
            NVIDIAAPIClient(api_key="")

    def test_client_creation(self):
        client = NVIDIAAPIClient(api_key="nvapi-test-key")
        assert client.api_key == "nvapi-test-key"
        assert client.timeout == 120.0