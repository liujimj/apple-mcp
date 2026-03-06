"""Shared AppleScript runner utility."""

from __future__ import annotations

import subprocess


def escape(text: str) -> str:
    """Escape a string for safe embedding in AppleScript."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


class AppleScriptError(Exception):
    """An AppleScript execution failed."""

    def __init__(self, message: str):
        # Strip the raw script from osascript error messages — keep only the
        # human-readable part (e.g. "execution error: ... (-1728)")
        clean = message
        # osascript errors look like "NN:MM: execution error: ..."
        if "execution error:" in clean:
            clean = clean[clean.index("execution error:") :]
        super().__init__(clean)


def run(script: str, *, timeout: int = 30) -> str:
    """Execute an AppleScript and return its stdout.

    Raises AppleScriptError on non-zero exit or timeout.
    """
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise AppleScriptError(f"AppleScript timed out after {timeout}s") from None

    if result.returncode != 0:
        raise AppleScriptError(result.stderr.strip())
    return result.stdout.strip()
