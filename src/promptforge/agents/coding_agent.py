"""Coding Agent."""
from typing import Any
from promptforge.agents.base_agent import BaseAgent
from promptforge.models.schemas import AgentType

CODE_SYSTEM_PROMPT = "You are a senior software engineer. Write complete, production-quality code."


class CodingAgent(BaseAgent):
    agent_type = AgentType.CODING

    async def plan(self) -> list[dict[str, Any]]:
        return [
            {"name": "analyze_requirements", "action": "parse_requirements"},
            {"name": "generate_code", "action": "write_code"},
            {"name": "validate_syntax", "action": "check_syntax"},
        ]

    async def execute_step(self, step: dict[str, Any]) -> dict[str, Any]:
        nvidia = self._get_nvidia()
        if not nvidia:
            return {"error": "NVIDIA API not available"}
        action = step.get("action", "")
        if action == "parse_requirements":
            result = await nvidia.chat_completion(
                messages=[{"role": "system", "content": "You are a software architect."}, {"role": "user", "content": f"Analyze requirements: {self.description}"}],
                model=self.config.default_model,
            )
            return {"requirements": result.get("content", "")}
        elif action == "write_code":
            context = self._memory.get("analyze_requirements", {}).get("requirements", "")
            result = await nvidia.chat_completion(
                messages=[{"role": "system", "content": CODE_SYSTEM_PROMPT}, {"role": "user", "content": f"Task: {self.description}. Context: {context[:3000]}"}],
                model=self.config.default_model,
                max_tokens=8192,
            )
            return {"code": result.get("content", "")}
        elif action == "check_syntax":
            code = self._memory.get("generate_code", {}).get("code", "")
            if not code.strip():
                return {"error": "Empty code output"}
            fence = chr(96) * 3
            if fence in code:
                parts = code.split(fence)
                if len(parts) >= 3:
                    code = parts[1]
            if len(code) < 20:
                return {"error": "Code too short"}
            return {"valid": True, "code": code}
        return {"error": f"Unknown action: {action}"}

    async def verify(self, outputs: dict[str, Any]) -> bool:
        code_result = outputs.get("validate_syntax", {})
        if code_result.get("error"):
            return False
        code = code_result.get("code", "")
        return len(code) > 50