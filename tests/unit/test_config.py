"""Tests for EngineConfig."""
from promptforge.core.config import EngineConfig


class TestEngineConfig:
    def test_default_values(self):
        config = EngineConfig(nvidia_api_key="test", github_token="test")
        assert config.default_model == "glm-5.2"
        assert config.max_concurrent_agents == 5

    def test_validate_credentials(self):
        config = EngineConfig(nvidia_api_key="test", github_token="test")
        creds = config.validate_credentials()
        assert creds["nvidia"] is True
        assert creds["github"] is True

    def test_missing_credentials(self):
        config = EngineConfig(nvidia_api_key="", github_token="")
        creds = config.validate_credentials()
        assert creds["nvidia"] is False
        assert creds["github"] is False