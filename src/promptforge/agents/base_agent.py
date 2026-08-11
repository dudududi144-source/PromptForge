"""Base Agent."""
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any

from promptforge.core.config import EngineConfig
from promptforge.models.schemas import AgentResult, AgentType


class BaseAgent(ABC):
    """Abstract base class for all agents."""
    agent_type: AgentType = AgentType.CODING

    def __init__(self, task_id: str, description: str, config: EngineConfig,
                 dependencies: list[str] | None = None, integration_hub: Any = None):
        self.task_id = task_id
        self.description = description
        self.config = config
        self.dependencies = dependencies or []
        self.integration_hub = integration_hub
        self._memory: dict[str, Any] = {}

    @abstractmethod
    async def plan(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def execute_step(self, step: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    async def verify(self, outputs: dict[str, Any]) -> bool: ...

    async def execute(self) -> AgentResult:
        start = time.monotonic()
        try:
            steps = await self.plan()
            outputs: dict[str, Any] = {}
            for step in steps:
                result = await asyncio.wait_for(self.execute_step(step), timeout=self.config.agent_timeout_sec)
                outputs[step.get("name", "unnamed")] = result
                self._memory[step.get("name", "unnamed")] = result
                if isinstance(result, dict) and result.get("error"):
                    return AgentResult(task_id=self.task_id, agent_type=self.agent_type, success=False, output=outputs, error=result["error"])
            is_valid = await self.verify(outputs)
            return AgentResult(task_id=self.task_id, agent_type=self.agent_type, success=is_valid, output=outputs)
        except asyncio.TimeoutError:
            return AgentResult(task_id=self.task_id, agent_type=self.agent_type, success=False, error=f"Timeout after {self.config.agent_timeout_sec}s")
        except Exception as exc:
            return AgentResult(task_id=self.task_id, agent_type=self.agent_type, success=False, error=str(exc))

    def _get_nvidia(self):
        if self.integration_hub:
            return self.integration_hub._init_nvidia()
        return None