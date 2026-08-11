"""Testing Agent."""
from typing import Any
from promptforge.agents.base_agent import BaseAgent
from promptforge.models.schemas import AgentType


class TestingAgent(BaseAgent):
    agent_type = AgentType.TESTING

    async def plan(self) -> list[dict[str, Any]]:
        return [
            {"name": "generate_tests", "action": "write_tests"},
            {"name": "validate_tests", "action": "check_test_quality"},
        ]

    async def execute_step(self, step: dict[str, Any]) -> dict[str, Any]:
        nvidia = self._get_nvidia()
        if not nvidia:
            return {"error": "NVIDIA API not available"}
        action = step.get("action", "")
        if action == "write_tests":
            result = await nvidia.chat_completion(
                messages=[{"role": "system", "content": "You are a test automation expert. Write pytest tests."}, {"role": "user", "content": f"Write tests for: {self.description}"}],
                model=self.config.default_model,
                max_tokens=6144,
            )
            return {"tests": result.get("content", "")}
        elif action == "check_test_quality":
            tests = self._memory.get("generate_tests", {}).get("tests", "")
            issues = []
            if "def test_" not in tests:
                issues.append("No test functions found")
            if "assert" not in tests:
                issues.append("No assertions found")
            if issues:
                return {"error": "; ".join(issues)}
            return {"quality": "pass", "test_count": tests.count("def test_")}
        return {"error": f"Unknown action: {action}"}

    async def verify(self, outputs: dict[str, Any]) -> bool:
        return outputs.get("validate_tests", {}).get("quality") == "pass"