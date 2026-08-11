"""PromptForge Chat UI."""
from typing import Any


class ChatUI:
    """PromptForge Chat UI - frontend for code generation."""

    def __init__(self, gateway):
        self.gateway = gateway

    async def generate(self, goal: str, pipeline: str = "full") -> dict[str, Any]:
        """Generate code from a goal."""
        return await self.gateway.handle_generate(goal, pipeline)

    async def health(self) -> dict[str, Any]:
        """Check system health."""
        return await self.gateway.handle_health()