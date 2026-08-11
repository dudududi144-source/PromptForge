"""PromptForge Gateway Worker."""
import asyncio
import json
import time
from typing import Any

from promptforge.core.config import EngineConfig
from promptforge.core.engine import PromptForgeEngine
from promptforge.core.observability import (
    HealthChecker, MetricsCollector, StructuredLogger,
    generate_request_id, request_id_var,
)
from promptforge.core.resilience import CircuitBreaker, RateLimiter
from promptforge.models.schemas import PipelineType

logger = StructuredLogger("promptforge.gateway")
metrics = MetricsCollector()
health_checker = HealthChecker()
rate_limiter = RateLimiter(max_requests=60, window_seconds=60)
circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)


class GatewayWorker:
    """PromptForge Gateway Worker - entry point for all requests."""

    def __init__(self, config: EngineConfig):
        self.config = config
        self.engine = PromptForgeEngine(config)

    async def handle_generate(self, goal: str, pipeline: str = "full") -> dict[str, Any]:
        """Handle code generation request."""
        request_id = generate_request_id()
        request_id_var.set(request_id)

        # Rate limiting
        client_ip = "unknown"
        if not rate_limiter.is_allowed(client_ip):
            return {"error": "Rate limit exceeded", "retry_after": 60}

        # Circuit breaker
        if not circuit_breaker.can_execute():
            return {"error": "Service temporarily unavailable", "retry_after": 60}

        start_time = time.monotonic()
        try:
            pipeline_type = PipelineType(pipeline)
            result = await self.engine.execute_task(goal, pipeline_type)
            circuit_breaker.record_success()
            duration_ms = int((time.monotonic() - start_time) * 1000)
            metrics.record("request.duration", duration_ms, {"endpoint": "generate"})
            metrics.record("request.count", 1, {"endpoint": "generate"})
            logger.info("Request completed", request_id=request_id, duration_ms=duration_ms)
            return result.model_dump()
        except Exception as e:
            circuit_breaker.record_failure()
            duration_ms = int((time.monotonic() - start_time) * 1000)
            metrics.record("request.errors", 1, {"endpoint": "generate"})
            logger.error("Request failed", request_id=request_id, error=str(e))
            return {"error": str(e)}

    async def handle_health(self) -> dict[str, Any]:
        """Handle health check request."""
        return await health_checker.run_checks()

    async def shutdown(self) -> None:
        """Shutdown the gateway."""
        await self.engine.shutdown()
        logger.info("Gateway shutdown complete")