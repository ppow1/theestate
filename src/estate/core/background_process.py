"""Process helpers for explicitly background Estate runtime work.

Interactive and foreground commands should continue to call ``subprocess``
directly.  These helpers are only for commands owned by a background runtime
and preserve normal output, exit-code, and timeout behavior.
"""
from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import Any


def hidden_windows_process_kwargs() -> dict[str, Any]:
    """Return Windows-only no-window flags, or nothing on other platforms."""
    if os.name != "nt":
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return {
        "creationflags": subprocess.CREATE_NO_WINDOW,
        "startupinfo": startupinfo,
    }


def direct_argv(command: str) -> list[str] | None:
    """Parse a command only when it does not require a shell.

    Shell syntax remains supported for recipes that need it.  Simple commands
    such as ``pytest -q tests/...`` are invoked directly and therefore do not
    acquire Windows' implicit ``cmd.exe /c`` wrapper.
    """
    if not command.strip() or any(char in command for char in "&|<>^()%!"):
        return None
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return None


def run_background_command(
    command: str,
    *,
    cwd: Path,
    env: dict[str, str],
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a background recipe with hidden Windows process creation."""
    argv = direct_argv(command) if os.name == "nt" else None
    kwargs: dict[str, Any] = {
        "cwd": cwd,
        "text": True,
        "capture_output": True,
        "env": env,
        "check": False,
        "timeout": timeout,
        **hidden_windows_process_kwargs(),
    }
    if argv is None:
        kwargs["shell"] = True
        invocation: str | list[str] = command
    else:
        kwargs["shell"] = False
        invocation = argv
    if timeout is None:
        kwargs.pop("timeout")
    return subprocess.run(invocation, **kwargs)


def hidden_background_popen_kwargs() -> dict[str, Any]:
    """Return no-window options for a detached background child process."""
    return {
        **hidden_windows_process_kwargs(),
        "start_new_session": os.name != "nt",
    }
