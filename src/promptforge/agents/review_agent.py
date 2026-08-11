"""Review Agent."""
from typing import Any
from promptforge.agents.base_agent import BaseAgent
from promptforge.models.schemas import AgentType


class ReviewAgent(BaseAgent):
    agent_type = AgentType.REVIEW

    async def plan(self) -> list[dict[str, Any]]:
        return [
            {"name": "security_scan", "action": "check_security"},
            {"name": "quality_review", "action": "check_quality"},
            {"name": "final_verdict", "action": "synthesize_review"},
        ]

    async def execute_step(self, step: dict[str, Any]) -> dict[str, Any]:
        nvidia = self._get_nvidia()
        if not nvidia:
            return {"error": "NVIDIA API not available"}
        action = step.get("action", "")
        if action == "check_security":
            result = await nvidia.chat_completion(
                messages=[{"role": "system", "content": "You are a security auditor."}, {"role": "user", "content": f"Security review: {self.description}"}],
                model=self.config.default_model,
            )
            content = result.get("content", "")
            has_critical = "critical" in content.lower()
            return {"findings": content, "has_critical": has_critical, "score": 0 if has_critical else 80}
        elif action == "check_quality":
            result = await nvidia.chat_completion(
                messages=[{"role": "system", "content": "You are a code quality reviewer."}, {"role": "user", "content": f"Quality review: {self.description}"}],
                model=self.config.default_model,
            )
            return {"review": result.get("content", ""), "score": 75}
        elif action == "synthesize_review":
            security = self._memory.get("security_scan", {})
            quality = self._memory.get("quality_review", {})
            overall = min(security.get("score", 50), quality.get("score", 50))
            return {"overall_score": overall, "approved": overall >= 70}
        return {"error": f"Unknown action: {action}"}

    async def verify(self, outputs: dict[str, Any]) -> bool:
        verdict = outputs.get("final_verdict", {})
        return verdict.get("approved", False) and verdict.get("overall_score", 0) >= 70