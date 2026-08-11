"""PromptForge Core Engine."""
import asyncio
import logging
import time
from typing import Any, Optional

from promptforge.core.config import EngineConfig
from promptforge.core.supervisor import SupervisorOrchestrator
from promptforge.models.schemas import ExecutionResult, PipelineType

logger = logging.getLogger("promptforge.engine")


class PromptForgeEngine:
    """The central orchestration engine."""

    def __init__(self, config: EngineConfig):
        self.config = config
        self.supervisor = SupervisorOrchestrator(config)
        self._running = False

    async def execute_task(
        self, goal: str, pipeline: PipelineType = PipelineType.FULL, dry_run: bool = False
    ) -> ExecutionResult:
        """Execute a full pipeline for the given goal."""
        start_time = time.monotonic()
        self._running = True
        try:
            spec = await self.supervisor.plan(goal, pipeline)
            if dry_run:
                return ExecutionResult(
                    pipeline=pipeline, goal=goal, success=True,
                    outputs={"plan": spec.model_dump()},
                )
            agents = await self.supervisor.spawn_agents(spec)
            results = await self.supervisor.execute_parallel(agents, spec)
            integrated = await self.supervisor.integrate(results)
            return ExecutionResult(
                pipeline=pipeline, goal=goal,
                success=all(r.success for r in results.values()),
                agents_used=[r.agent_type.value for r in results.values()],
                total_tokens=sum(r.tokens_used for r in results.values()),
                outputs=integrated,
                errors=[r.error for r in results.values() if r.error],
            )
        except Exception as exc:
            logger.error(f"Pipeline failed: {exc}", exc_info=True)
            return ExecutionResult(pipeline=pipeline, goal=goal, success=False, errors=[str(exc)])
        finally:
            self._running = False

    async def shutdown(self) -> None:
        self._running = False
        await self.supervisor.shutdown()