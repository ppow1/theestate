from __future__ import annotations

import subprocess
import sys
from types import SimpleNamespace

import pytest

from estate.core import background_process


def test_direct_pytest_command_avoids_shell_wrapper_on_windows(monkeypatch):
    calls = []

    monkeypatch.setattr(background_process.os, "name", "nt")
    monkeypatch.setattr(background_process.subprocess, "STARTUPINFO", lambda: SimpleNamespace(dwFlags=0, wShowWindow=None))
    monkeypatch.setattr(background_process.subprocess, "STARTF_USESHOWWINDOW", 1)
    monkeypatch.setattr(background_process.subprocess, "SW_HIDE", 0)
    monkeypatch.setattr(background_process.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "ok\n", "warning\n")

    monkeypatch.setattr(background_process.subprocess, "run", fake_run)
    result = background_process.run_background_command(
        "pytest -q tests/test_operational.py",
        cwd=__import__("pathlib").Path("."),
        env={},
    )

    command, kwargs = calls[0]
    assert result.returncode == 0
    assert command == ["pytest", "-q", "tests/test_operational.py"]
    assert kwargs["shell"] is False
    assert kwargs["creationflags"] == 0x08000000
    assert kwargs["startupinfo"].wShowWindow == 0
    assert kwargs["capture_output"] is True


def test_shell_recipe_still_uses_hidden_windows_creation(monkeypatch):
    calls = []
    monkeypatch.setattr(background_process.os, "name", "nt")
    monkeypatch.setattr(background_process.subprocess, "STARTUPINFO", lambda: SimpleNamespace(dwFlags=0, wShowWindow=None))
    monkeypatch.setattr(background_process.subprocess, "STARTF_USESHOWWINDOW", 1)
    monkeypatch.setattr(background_process.subprocess, "SW_HIDE", 0)
    monkeypatch.setattr(background_process.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)
    monkeypatch.setattr(background_process.subprocess, "run", lambda command, **kwargs: calls.append((command, kwargs)) or subprocess.CompletedProcess(command, 3, "out", "err"))

    result = background_process.run_background_command("pytest -q tests/a.py && echo done", cwd=__import__("pathlib").Path("."), env={})

    assert result.returncode == 3
    assert calls[0][0] == "pytest -q tests/a.py && echo done"
    assert calls[0][1]["shell"] is True
    assert calls[0][1]["creationflags"] == 0x08000000


def test_non_windows_preserves_shell_execution(monkeypatch):
    calls = []
    monkeypatch.setattr(background_process.os, "name", "posix")
    monkeypatch.setattr(background_process.subprocess, "run", lambda command, **kwargs: calls.append((command, kwargs)) or subprocess.CompletedProcess(command, 0, "out", "err"))

    background_process.run_background_command("pytest -q tests/a.py", cwd=__import__("pathlib").Path("."), env={})

    assert calls[0][0] == "pytest -q tests/a.py"
    assert calls[0][1]["shell"] is True
    assert "creationflags" not in calls[0][1]


@pytest.mark.parametrize("code", [0, 7])
def test_background_command_preserves_output_and_exit_code(monkeypatch, code):
    monkeypatch.setattr(background_process.os, "name", "posix")
    command = f'"{sys.executable}" -c "print(\'out\'); import sys; print(\'err\', file=sys.stderr); sys.exit({code})"'
    result = background_process.run_background_command(command, cwd=__import__("pathlib").Path("."), env={})
    assert result.returncode == code
    assert "out" in result.stdout
    assert "err" in result.stderr
