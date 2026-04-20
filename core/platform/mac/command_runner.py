"""Shared command execution helpers for macOS platform adapters."""

from __future__ import annotations

from dataclasses import dataclass
import subprocess


class CommandRunnerError(RuntimeError):
    """Raised when a platform command cannot be executed successfully."""


@dataclass(slots=True, frozen=True)
class CommandResult:
    """Captured command execution result."""

    args: tuple[str, ...]
    returncode: int
    stdout: bytes
    stderr: bytes

    def require_success(self) -> "CommandResult":
        """Raise with stderr context if the command failed."""

        if self.returncode != 0:
            detail = self.stderr.decode("utf-8", errors="replace").strip()
            raise CommandRunnerError(detail or f"command failed: {' '.join(self.args)}")
        return self


def run_command(args: list[str] | tuple[str, ...], timeout_seconds: float = 30.0) -> CommandResult:
    """Run a command and capture raw stdout/stderr bytes."""

    completed = subprocess.run(
        tuple(args),
        check=False,
        capture_output=True,
        timeout=timeout_seconds,
    )
    return CommandResult(
        args=tuple(args),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
