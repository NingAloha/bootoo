"""Domain result skeleton."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class StepResult:
    step_id: str
    ok: bool
    message: str = ""


@dataclass(slots=True)
class ExecutionResult:
    ok: bool
    code: str
    message: str
    steps: list[StepResult] = field(default_factory=list)
