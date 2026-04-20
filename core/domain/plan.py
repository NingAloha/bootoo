"""Execution plan domain model skeleton."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class PlanStep:
    identifier: str
    kind: str
    description: str


@dataclass(slots=True)
class ExecutionPlan:
    mode: str
    steps: list[PlanStep] = field(default_factory=list)
