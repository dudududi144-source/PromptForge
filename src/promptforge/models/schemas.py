"""Pydantic data models."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class PipelineType(str, Enum):
    FULL = "full"
    CODE_ONLY = "code_only"
    RESEARCH = "research"
    REVIEW = "review"


class AgentType(str, Enum):
    RESEARCH = "research"
    CODING = "coding"
    TESTING = "testing"
    REVIEW = "review"


class TaskItem(BaseModel):
    id: str
    type: AgentType
    description: str
    dependencies: list[str] = Field(default_factory=list)


class TaskSpec(BaseModel):
    goal: str
    tasks: list[TaskItem]
    estimated_total_tokens: int = Field(default=50000, ge=0)


class AgentResult(BaseModel):
    task_id: str
    agent_type: AgentType
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    tokens_used: int = Field(default=0, ge=0)


class ExecutionResult(BaseModel):
    pipeline: PipelineType
    goal: str
    success: bool
    agents_used: list[str] = Field(default_factory=list)
    total_tokens: int = Field(default=0, ge=0)
    outputs: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)