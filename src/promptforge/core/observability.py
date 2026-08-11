"""Observability & Monitoring."""
import logging
import time
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Optional

request_id_var: ContextVar[str] = ContextVar("request_id")


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


class StructuredLogger:
    """Structured logger with request context."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _get_context(self) -> dict[str, Any]:
        return {
            "request_id": request_id_var.get("unknown"),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def info(self, message: str, **kwargs) -> None:
        context = self._get_context()
        context.update(kwargs)
        self.logger.info(f"{message} | {context}")

    def error(self, message: str, **kwargs) -> None:
        context = self._get_context()
        context.update(kwargs)
        self.logger.error(f"{message} | {context}")

    def warning(self, message: str, **kwargs) -> None:
        context = self._get_context()
        context.update(kwargs)
        self.logger.warning(f"{message} | {context}")


class MetricsCollector:
    """Collect and store metrics."""

    def __init__(self):
        self.metrics: list[dict[str, Any]] = []

    def record(self, name: str, value: float, tags: dict[str, str] = None) -> None:
        self.metrics.append({
            "name": name,
            "value": value,
            "tags": tags or {},
            "timestamp": datetime.utcnow().isoformat(),
        })

    def get_metrics(self, name: str = None) -> list[dict[str, Any]]:
        if name:
            return [m for m in self.metrics if m["name"] == name]
        return self.metrics


class HealthChecker:
    """Health check endpoint."""

    def __init__(self):
        self.checks: dict[str, Any] = {}

    def register(self, name: str, check_func) -> None:
        self.checks[name] = check_func

    async def run_checks(self) -> dict[str, Any]:
        results = {}
        for name, check_func in self.checks.items():
            try:
                results[name] = await check_func()
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
        all_healthy = all(r.get("status") != "error" for r in results.values())
        return {
            "status": "healthy" if all_healthy else "degraded",
            "checks": results,
            "timestamp": datetime.utcnow().isoformat(),
        }