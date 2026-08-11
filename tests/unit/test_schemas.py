"""Tests for data models."""
import pytest
from promptforge.models.schemas import (
    AgentResult, AgentType, ExecutionResult, PipelineType, TaskItem, TaskSpec,
)


class TestTaskSpec:
    def test_create_task_spec(self):
        spec = TaskSpec(goal="Build a REST API", tasks=[TaskItem(id="task_1", type=AgentType.CODING, description="Implement endpoints")])
        assert spec.goal == "Build a REST API"
        assert len(spec.tasks) == 1


class TestAgentResult:
    def test_successful_result(self):
        result = AgentResult(task_id="t1", agent_type=AgentType.CODING, success=True, output={"code": "x=1"})
        assert result.success is True
        assert result.error is None

    def test_failed_result(self):
        result = AgentResult(task_id="t2", agent_type=AgentType.TESTING, success=False, error="fail")
        assert result.success is False
        assert result.error == "fail"


class TestExecutionResult:
    def test_create_result(self):
        result = ExecutionResult(pipeline=PipelineType.FULL, goal="Build X", success=True)
        assert result.success is True
        assert result.pipeline == PipelineType.FULL