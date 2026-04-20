"""Public API skeleton for bootoo."""

from dataclasses import dataclass


class SkeletonOnlyError(NotImplementedError):
    """Raised when a placeholder API surface is invoked."""


@dataclass(slots=True)
class APIStatus:
    ok: bool
    code: str
    message: str


def not_ready(name: str) -> APIStatus:
    return APIStatus(
        ok=False,
        code="SKELETON_ONLY",
        message=f"{name} is not implemented in the redesigned skeleton yet.",
    )
