"""Supervisor Orchestrator."""
import asyncio
import logging
from typing import Any

from promptforge.core.config import EngineConfig
from promptforge.models.schemas import AgentResult, AgentType, PipelineType, TaskItem, TaskSpec

logger = logging.getLogger("promptforge.supervisor")


class IntegrationHub:
    """Central hub for all external integrations."""

    def __init__(self, config: EngineConfig):
        self.config = config
        self.nvidia = None

    def _init_nvidia(self):
        if self.nvidia is None:
            from promptforge.integrations.nvidia_api import NVIDIAAPIClient
            self.nvidia = NVIDIAAPIClient(self.config.nvidia_api_key)
        return self.nvidia

    async def health_check(self) -> dict[str, bool]:
        checks = {}
        try:
            checks["nvidia"] = await self._init_nvidia().ping()
        except Exception:
            checks["nvidia"] = False
        checks["github"] = bool(self.config.github_token)
        return checks


class SupervisorOrchestrator:
    """Supervisor pattern orchestrator."""

    def __init__(self, config: EngineConfig):
        self.config = config
        self.integration_hub = IntegrationHub(config)
        self._agent_registry: dict[str, type] = {}
        self._register_default_agents()

    def _register_default_agents(self) -> None:
        from promptforge.agents.coding_agent import CodingAgent
        from promptforge.agents.research_agent import ResearchAgent
        from promptforge.agents.review_agent import ReviewAgent
        from promptforge.agents.testing_agent import TestingAgent
        self._agent_registry = {
            AgentType.RESEARCH.value: ResearchAgent,
            AgentType.CODING.value: CodingAgent,
            AgentType.TESTING.value: TestingAgent,
            AgentType.REVIEW.value: ReviewAgent,
        }

    async def plan(self, goal: str, pipeline: PipelineType) -> TaskSpec:
        """Decompose goal into tasks."""
        try:
            nvidia = self.integration_hub._init_nvidia()
            prompt = f"Decompose this goal into tasks: {goal}. Respond JSON."
            result = await nvidia.structured_output(prompt, task_type="planning")
            tasks = []
            for i, t in enumerate(result.get("tasks", [])):
                try:
                    agent_type = AgentType(t.get("type", "coding"))
                except ValueError:
                    agent_type = AgentType.CODING
                tasks.append(TaskItem(id=t.get("id", f"task_{i}"), type=agent_type, description=t.get("description", f"Task {i}")))
            if not tasks:
                return self._fallback_plan(goal, pipeline)
            return TaskSpec(goal=goal, tasks=tasks)
        except Exception as exc:
            logger.warning(f"LLM planning failed ({exc}), using fallback")
            return self._fallback_plan(goal, pipeline)

    def _fallback_plan(self, goal: str, pipeline: PipelineType) -> TaskSpec:
        tasks = []
        if pipeline in (PipelineType.FULL, PipelineType.RESEARCH):
            tasks.append(TaskItem(id="task_research", type=AgentType.RESEARCH, description=f"Research: {goal}"))
        if pipeline in (PipelineType.FULL, PipelineType.CODE_ONLY):
            deps = ["task_research"] if tasks else []
            tasks.append(TaskItem(id="task_code", type=AgentType.CODING, description=f"Implement: {goal}", dependencies=deps))
        if pipeline == PipelineType.FULL:
            tasks.append(TaskItem(id="task_test", type=AgentType.TESTING, description=f"Test: {goal}", dependencies=["task_code"]))
            tasks.append(TaskItem(id="task_review", type=AgentType.REVIEW, description=f"Review: {goal}", dependencies=["task_test"]))
        return TaskSpec(goal=goal, tasks=tasks)

    async def spawn_agents(self, spec: TaskSpec) -> list[Any]:
        agents = []
        for task in spec.tasks:
            agent_cls = self._agent_registry.get(task.type.value)
            if agent_cls:
                agents.append(agent_cls(task_id=task.id, description=task.description, config=self.config, dependencies=task.dependencies, integration_hub=self.integration_hub))
        return agents

    async def execute_parallel(self, agents: list[Any], spec: TaskSpec) -> dict[str, AgentResult]:
        semaphore = asyncio.Semaphore(self.config.max_concurrent_agents)
        results: dict[str, AgentResult] = {}
        completed_ids: set[str] = set()
        remaining = list(agents)
        for _round in range(len(agents) + 1):
            ready = [a for a in remaining if all(d in completed_ids for d in a.dependencies)]
            if not ready:
                break
            async def _run(agent):
                async with semaphore:
                    return await agent.execute()
            batch = await asyncio.gather(*[_run(a) for a in ready], return_exceptions=True)
            for agent, res in zip(ready, batch):
                if isinstance(res, Exception):
                    results[agent.task_id] = AgentResult(task_id=agent.task_id, agent_type=agent.agent_type, success=False, error=str(res))
                else:
                    results[agent.task_id] = res
                completed_ids.add(agent.task_id)
                remaining.remove(agent)
        return results

    async def integrate(self, results: dict[str, AgentResult]) -> dict[str, Any]:
        return {tid: (r.output if r.success else {"error": r.error}) for tid, r in results.items()}

    async def shutdown(self) -> None:
        logger.info("Supervisor shutting down")