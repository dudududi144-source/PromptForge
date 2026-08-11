"""Research Agent."""
from typing import Any
from promptforge.agents.base_agent import BaseAgent
from promptforge.models.schemas import AgentType


class ResearchAgent(BaseAgent):
    agent_type = AgentType.RESEARCH

    async def plan(self) -> list[dict[str, Any]]:
        return [
            {"name": "gather_context", "action": "analyze_goal"},
            {"name": "summarize_findings", "action": "synthesize"},
        ]

    async def execute_step(self, step: dict[str, Any]) -> dict[str, Any]:
        nvidia = self._get_nvidia()
        if not nvidia:
            return {"error": "NVIDIA API not available"}
        action = step.get("action", "")
        if action == "analyze_goal":
            result = await nvidia.chat_completion(
                messages=[{"role": "system", "content": "You are a senior technical researcher."}, {"role": "user", "content": f"Analyze this goal: {self.description}"}],
                model=self.config.default_model,
            )
            return {"analysis": result.get("content", "")}
        elif action == "synthesize":
            context = self._memory.get("gather_context", {}).get("analysis", "")
            result = await nvidia.chat_completion(
                messages=[{"role": "system", "content": "You are a technical writer."}, {"role": "user", "content": f"Summarize: {context[:2000]}"}],
                model=self.config.default_model,
            )
            return {"briefing": result.get("content", "")}
        return {"error": f"Unknown action: {action}"}

    async def verify(self, outputs: dict[str, Any]) -> bool:
        briefing = outputs.get("summarize_findings", {}).get("briefing", "")
        return len(briefing) > 50