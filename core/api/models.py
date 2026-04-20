"""API request/response model placeholders."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class APIRequest:
    command: str
    options: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class APIResponse:
    ok: bool
    code: str
    message: str
    data: dict[str, object] = field(default_factory=dict)
