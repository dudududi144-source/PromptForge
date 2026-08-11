"""PromptForge Configuration."""
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class EngineConfig(BaseSettings):
    """Central configuration for PromptForge."""
    nvidia_api_key: str = Field(default="")
    github_token: str = Field(default="")
    supabase_url: str = Field(default="")
    supabase_key: str = Field(default="")
    default_model: str = Field(default="glm-5.2")
    max_concurrent_agents: int = Field(default=5, ge=1, le=20)
    agent_timeout_sec: int = Field(default=300, ge=30, le=3600)

    model_config = {"env_file": ".env", "env_prefix": "PROMPTFORGE_", "case_sensitive": False}

    def validate_credentials(self) -> dict[str, bool]:
        return {"nvidia": bool(self.nvidia_api_key), "github": bool(self.github_token)}