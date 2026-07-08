"""Conservative local Codex CLI bridge.

This module implements a bounded `codex exec` adapter. It intentionally does
not implement Codex Cloud apply, unrestricted sandboxing, or arbitrary CLI
argument passthrough.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import uuid
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

from estate.core.paths import ESTATE_ROOT

RUNTIME_RELATIVE_DIR = Path("runtime/codex_bridge")
DEFAULT_CODEX_BINARY = "codex"
APPROVAL_POLICY = "never"
SANDBOX_READ_ONLY = "read-only"
SANDBOX_WORKSPACE_WRITE = "workspace-write"
PROHIBITED_SANDBOX = "danger-full-access"
ALLOWED_SANDBOXES = {SANDBOX_READ_ONLY, SANDBOX_WORKSPACE_WRITE}
ALLOWED_PROVIDER_PROFILES = {
    "codex-cli-openai": {"default", "chatgpt-business-default", "sandbox-offline"},
    "codex-cli-ollama": {"default", "local-ollama"},
}
FORBIDDEN_PATH_SEGMENTS = {".git", ".codex", "runtime"}
FORBIDDEN_FILE_NAMES = {".env", "auth.json"}
MOJIBAKE_MARKERS = ("ΓÇÖ", "ΓÇ£", "ΓÇ¥", "ΓÇô", "ΓÇö", "├⌐", "├»", "├▒")
EVENT_TYPES = {
    "job_accepted",
    "execution_started",
    "checkpoint_reached",
    "waiting_for_approval",
    "validation_started",
    "validation_passed",
    "validation_failed",
    "commit_created",
    "result_returned",
    "execution_complete",
    "execution_failed",
    "policy_denied",
}
PRESERVED_KNOWN_LIMITATIONS = [
    "Non-interactive /status automation is unknown.",
    "Authenticated multi-seat concurrency is unknown.",
    "Codex Cloud task lifecycle is unknown.",
    "Codex Cloud apply is unapproved and blocked by this bridge.",
    "OpenAI-backed JSONL usage shape needs authenticated verification.",
    "Provider-level saturation and quota reporting may require a later capacity-monitoring package.",
    "Office of the Steward UI consumption may require a later integration package.",
]

ANSI_RE = re.compile(
    r"\x1b\[[0-?]*[ -/]*[@-~]"
    r"|\x1b\][^\x07]*(?:\x07|\x1b\\)"
    r"|\x1b[@-Z\\-_]"
)
CONTROL_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
SECRET_PATTERNS = [
    re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{10,}"),
    re.compile(r"(Bearer\s+)[A-Za-z0-9._~+/=-]{12,}", re.IGNORECASE),
    re.compile(r"((?:api[_-]?key|token|password|secret)\s*[:=]\s*)[^\s,;]+", re.IGNORECASE),
]


@dataclass
class CodexBridgeRequest:
    prompt_source: str | Path
    classification: str | None
    request_id: str = field(default_factory=lambda: f"cbr-{uuid.uuid4().hex[:12]}")
    work_package_id: str | None = None
    requested_by: str = "steward"
    provider: str = "codex-cli-openai"
    model: str | None = None
    codex_home_profile: str = "default"
    worker_label: str = "codex-bridge"
    cwd: str | Path | None = None
    sandbox: str = SANDBOX_READ_ONLY
    allowed_read_paths: list[str | Path] = field(default_factory=list)
    allowed_write_paths: list[str | Path] = field(default_factory=list)
    approval_policy: str = APPROVAL_POLICY
    json_mode: bool = True
    session_persistence_required: bool = False
    cloud_allowed: bool = False
    cloud_apply_requested: bool = False
    cloud_dispatch_requested: bool = False
    danger_full_access_requested: bool = False
    bypass_flags: list[str] = field(default_factory=list)
    validation_commands: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    attention_policy: str | None = None
    codex_binary: str = DEFAULT_CODEX_BINARY


@dataclass
class RequestValidation:
    accepted: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class CodexParsedOutput:
    mode: str
    final_message: str | None = None
    usage: dict[str, Any] | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    event_counts: dict[str, int] = field(default_factory=dict)
    failed_turns: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    parse_errors: list[str] = field(default_factory=list)
    telemetry: dict[str, Any] = field(default_factory=dict)


@dataclass
class CodexBridgeResult:
    request_id: str
    status: str
    started_at: str
    finished_at: str
    duration_seconds: float
    command: list[str]
    cwd: str
    provider: str
    model: str | None
    profile_label: str
    sandbox: str
    exit_code: int | None
    stdout: str
    stderr: str
    stdout_hash: str
    stderr_hash: str
    parsed_output: CodexParsedOutput
    usage: dict[str, Any] | None
    final_message: str | None
    lifecycle_events: list[dict[str, Any]]
    events_path: str | None
    status_snapshot_path: str | None
    audit_path: str | None
    changed_files: list[str]
    tests_run: list[str]
    known_limitations: list[str]
    promotion_recommendation: str
    validation_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))


def estate_root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _now_dt()).astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", value.strip())
    return safe[:120] or f"cbr-{uuid.uuid4().hex[:12]}"


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _resolve(path: str | Path | None, root: Path) -> Path:
    if path is None:
        return root.resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate.resolve(strict=False)


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _path_has_forbidden_segment(path: Path, root: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    if parts & FORBIDDEN_PATH_SEGMENTS:
        return True
    if path.name.lower() in FORBIDDEN_FILE_NAMES:
        return True
    if _is_relative_to(path, root):
        rel_parts = {part.lower() for part in path.relative_to(root).parts}
        return bool(rel_parts & FORBIDDEN_PATH_SEGMENTS) or path.name.lower() in FORBIDDEN_FILE_NAMES
    return False


def _path_is_too_broad(path: Path, root: Path) -> bool:
    if path == root:
        return True
    if path.anchor and str(path) == path.anchor:
        return True
    if path.name in {"", ".", "*"}:
        return True
    return False


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    return value


def redact_secrets(value: str) -> str:
    redacted = str(value)
    for pattern in SECRET_PATTERNS:
        if pattern.groups:
            redacted = pattern.sub(r"\1[REDACTED_SECRET]", redacted)
        else:
            redacted = pattern.sub("[REDACTED_SECRET]", redacted)
    return redacted


def _redact_tree(value: Any) -> Any:
    if isinstance(value, str):
        return redact_secrets(value)
    if isinstance(value, dict):
        return {k: _redact_tree(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact_tree(v) for v in value]
    return value


def _hash_bytes(raw: bytes | str | None) -> str:
    if raw is None:
        raw = b""
    if isinstance(raw, str):
        raw = raw.encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()


def _hash_file(path: Path) -> str | None:
    try:
        return _hash_bytes(path.read_bytes())
    except OSError:
        return None


def recover_cp437_mojibake(text: str) -> str:
    if not any(marker in text for marker in MOJIBAKE_MARKERS):
        return text
    try:
        candidate = text.encode("cp437").decode("utf-8")
    except UnicodeError:
        return text
    return candidate if "�" not in candidate else text


def strip_terminal_controls(text: str) -> str:
    text = ANSI_RE.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return CONTROL_RE.sub("", text)


def normalize_text(text: str | bytes | None) -> str:
    if text is None:
        return ""
    if isinstance(text, bytes):
        return normalize_bytes(text)
    text = recover_cp437_mojibake(text)
    return strip_terminal_controls(text)


def normalize_bytes(raw: bytes | None) -> str:
    if raw is None:
        return ""
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError:
        decoded = raw.decode("utf-8", errors="replace")
        try:
            cp437 = raw.decode("cp437")
            if decoded.count("�") > cp437.count("�"):
                decoded = cp437
        except UnicodeError:
            pass
    return normalize_text(decoded)


def extract_text_usage(stderr: str) -> dict[str, int] | None:
    match = re.search(r"tokens\s+used\s*\n?\s*([\d,]+)", stderr, re.IGNORECASE)
    if not match:
        return None
    return {"tokens_used": int(match.group(1).replace(",", ""))}


def _extract_text_from_content(content: Any) -> str | None:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        pieces: list[str] = []
        for item in content:
            if isinstance(item, str):
                pieces.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if isinstance(text, str):
                    pieces.append(text)
        return "\n".join(pieces) if pieces else None
    return None


def _extract_agent_message(item: dict[str, Any]) -> str | None:
    if item.get("type") == "agent_message":
        return _extract_text_from_content(item.get("text") or item.get("message") or item.get("content"))
    if item.get("role") == "assistant":
        return _extract_text_from_content(item.get("content") or item.get("text"))
    nested = item.get("message")
    if isinstance(nested, dict) and nested.get("role") == "assistant":
        return _extract_text_from_content(nested.get("content") or nested.get("text"))
    return None


def parse_jsonl_output(stdout: str | bytes) -> CodexParsedOutput:
    text = normalize_text(stdout)
    parsed = CodexParsedOutput(mode="jsonl")
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            parsed.parse_errors.append(f"line {line_number}: {exc.msg}")
            continue
        if not isinstance(event, dict):
            parsed.parse_errors.append(f"line {line_number}: JSONL event is not an object")
            continue
        event_type = str(event.get("type") or "unknown")
        parsed.events.append(event)
        parsed.event_counts[event_type] = parsed.event_counts.get(event_type, 0) + 1
        if event_type == "thread.started":
            parsed.telemetry["thread_id"] = event.get("thread_id")
        elif event_type == "turn.started":
            parsed.telemetry["turn_started"] = True
        elif event_type == "item.completed":
            item = event.get("item") if isinstance(event.get("item"), dict) else event
            message = _extract_agent_message(item)
            if message is not None:
                parsed.final_message = normalize_text(message).strip()
        elif event_type == "turn.completed":
            usage = event.get("usage")
            if isinstance(usage, dict):
                parsed.usage = usage
        elif event_type == "turn.failed":
            failed = event.get("error") if isinstance(event.get("error"), dict) else event
            parsed.failed_turns.append(failed)
        elif event_type == "error":
            parsed.errors.append(event)
    return parsed


def parse_text_output(stdout: str | bytes, stderr: str | bytes = "") -> CodexParsedOutput:
    clean_stdout = normalize_text(stdout).strip()
    clean_stderr = normalize_text(stderr)
    return CodexParsedOutput(
        mode="text",
        final_message=clean_stdout,
        usage=extract_text_usage(clean_stderr),
        telemetry={"stderr": clean_stderr},
    )


def bridge_request_from_dict(data: dict[str, Any]) -> CodexBridgeRequest:
    allowed = {item.name for item in fields(CodexBridgeRequest)}
    values = {key: value for key, value in data.items() if key in allowed}
    return CodexBridgeRequest(**values)


def load_bridge_request(path: str | Path) -> CodexBridgeRequest:
    return bridge_request_from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def validate_bridge_request(request: CodexBridgeRequest, root: str | Path | None = None) -> RequestValidation:
    base = estate_root(root).resolve(strict=False)
    errors: list[str] = []
    warnings: list[str] = []

    if not request.classification or not str(request.classification).strip():
        errors.append("classification is required")

    if request.provider not in ALLOWED_PROVIDER_PROFILES:
        errors.append("provider profile is unknown")
    elif request.codex_home_profile not in ALLOWED_PROVIDER_PROFILES[request.provider]:
        errors.append("provider profile is unknown")

    if request.approval_policy != APPROVAL_POLICY:
        errors.append("approval policy must be never for bridge automation")

    if request.sandbox == PROHIBITED_SANDBOX or request.danger_full_access_requested:
        errors.append("danger-full-access is prohibited")
    elif request.sandbox not in ALLOWED_SANDBOXES:
        errors.append(f"sandbox must be one of {sorted(ALLOWED_SANDBOXES)}")

    if request.bypass_flags or any("bypass" in flag.lower() for flag in request.bypass_flags):
        errors.append("bypass flags are prohibited")

    if request.cloud_apply_requested:
        errors.append("cloud apply is prohibited")
    if request.cloud_dispatch_requested or request.cloud_allowed or "cloud" in request.provider.lower():
        errors.append("cloud execution is outside the local Codex Bridge v1 boundary")

    prompt_path = _resolve(request.prompt_source, base)
    if not prompt_path.exists():
        errors.append("prompt source does not exist")
    elif _path_has_forbidden_segment(prompt_path, base):
        errors.append("prompt source is inside a denied local runtime or secret path")

    read_paths = [_resolve(path, base) for path in request.allowed_read_paths]
    if not read_paths:
        errors.append("allowed read paths are required")
    elif prompt_path.exists() and not any(_is_relative_to(prompt_path, allowed) or prompt_path == allowed for allowed in read_paths):
        errors.append("prompt source is outside allowed read paths")

    cwd = _resolve(request.cwd, base)
    if not _is_relative_to(cwd, base) and cwd != base:
        errors.append("cwd must stay inside the Estate repository root")

    if request.sandbox == SANDBOX_WORKSPACE_WRITE:
        if not request.allowed_write_paths:
            errors.append("workspace-write requires explicit allowed write paths")
        for raw_path in request.allowed_write_paths:
            path = _resolve(raw_path, base)
            if not _is_relative_to(path, base) and path != base:
                errors.append(f"allowed write path is outside repository root: {raw_path}")
            if _path_is_too_broad(path, base):
                errors.append(f"allowed write path is too broad: {raw_path}")
            if _path_has_forbidden_segment(path, base):
                errors.append(f"allowed write path is denied by boundary policy: {raw_path}")
    elif request.allowed_write_paths:
        warnings.append("allowed write paths were provided for a read-only request and will be recorded only")

    if request.session_persistence_required and request.sandbox != SANDBOX_WORKSPACE_WRITE:
        errors.append("session persistence is only allowed for explicit workspace-write requests")

    return RequestValidation(accepted=not errors, errors=errors, warnings=warnings)


def build_codex_command(request: CodexBridgeRequest) -> list[str]:
    command = [request.codex_binary, "--ask-for-approval", request.approval_policy, "exec"]
    if request.provider == "codex-cli-ollama":
        command.extend(["--oss", "--local-provider", "ollama"])
    if request.model:
        command.extend(["-m", request.model])
    command.extend(["--sandbox", request.sandbox, "--color", "never"])
    if not request.session_persistence_required:
        command.append("--ephemeral")
    if request.json_mode:
        command.append("--json")
    command.append("-")
    return command


def _redacted_command(command: Sequence[str]) -> list[str]:
    redacted: list[str] = []
    redact_next = False
    for arg in command:
        if redact_next:
            redacted.append("[REDACTED_SECRET]")
            redact_next = False
            continue
        redacted.append(redact_secrets(arg))
        if arg.lower() in {"--api-key", "--token", "--password", "--secret"}:
            redact_next = True
    return redacted


def _execution_command(command: Sequence[str]) -> list[str]:
    if not command:
        return []
    executable = command[0]
    if Path(executable).is_absolute():
        return list(command)
    candidates = [executable]
    if os.name == "nt" and Path(executable).suffix == "":
        candidates = [f"{executable}.cmd", f"{executable}.exe", executable]
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return [resolved, *command[1:]]
    return list(command)


def _runtime_paths(root: Path, request_id: str) -> dict[str, Path]:
    safe = _safe_id(request_id)
    request_dir = root / RUNTIME_RELATIVE_DIR / safe
    return {
        "request_dir": request_dir,
        "events": request_dir / "events.jsonl",
        "status": request_dir / "status.json",
        "audit": request_dir / "audit.json",
        "current_status": root / RUNTIME_RELATIVE_DIR / "current_status.json",
    }


class LifecycleRecorder:
    def __init__(self, request: CodexBridgeRequest, root: Path, started_at: datetime):
        self.request = request
        self.root = root
        self.started_at = started_at
        self.paths = _runtime_paths(root, request.request_id)
        self.paths["request_dir"].mkdir(parents=True, exist_ok=True)
        self.events: list[dict[str, Any]] = []
        self.status_path: str | None = None

    def emit(
        self,
        event_type: str,
        *,
        state: str,
        summary: str,
        validation_status: str = "unknown",
        attention_required: bool = False,
    ) -> dict[str, Any]:
        if event_type not in EVENT_TYPES:
            raise ValueError(f"unsupported lifecycle event type: {event_type}")
        timestamp = _iso()
        elapsed = (_now_dt() - self.started_at).total_seconds()
        event = {
            "event_id": f"{self.request.request_id}-{len(self.events) + 1:04d}-{event_type}",
            "event_type": event_type,
            "request_id": self.request.request_id,
            "work_package_id": self.request.work_package_id,
            "worker_label": self.request.worker_label,
            "provider": self.request.provider,
            "current_state": state,
            "timestamp": timestamp,
            "elapsed_seconds": round(elapsed, 3),
            "security_classification": self.request.classification,
            "budget_source": self.request.codex_home_profile,
            "profile_label": self.request.codex_home_profile,
            "validation_status": validation_status,
            "human_attention_required": attention_required,
            "attention_required": attention_required,
            "summary": summary,
        }
        self.events.append(event)
        with self.paths["events"].open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(_redact_tree(event), sort_keys=True) + "\n")
        self.write_status_snapshot(event, state=state, validation_status=validation_status, attention_required=attention_required)
        return event

    def write_status_snapshot(
        self,
        event: dict[str, Any],
        *,
        state: str,
        validation_status: str,
        attention_required: bool,
    ) -> dict[str, Any]:
        snapshot = {
            "version": 1,
            "request_id": self.request.request_id,
            "worker": self.request.worker_label,
            "current_assignment": self.request.work_package_id or _rel(_resolve(self.request.prompt_source, self.root), self.root),
            "current_state": state,
            "elapsed_seconds": event.get("elapsed_seconds"),
            "estimated_completion": None,
            "provider": self.request.provider,
            "budget_source": self.request.codex_home_profile,
            "profile_label": self.request.codex_home_profile,
            "security_classification": self.request.classification,
            "validation_status": validation_status,
            "last_event": {"event_id": event["event_id"], "event_type": event["event_type"], "summary": event["summary"]},
            "attention_required": attention_required,
            "updated_at": event["timestamp"],
        }
        for path in (self.paths["status"], self.paths["current_status"]):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(_redact_tree(snapshot), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.status_path = _rel(self.paths["status"], self.root)
        return snapshot


def _read_prompt(path: Path) -> str:
    return normalize_bytes(path.read_bytes())


def _git_changed_files(root: Path) -> list[str]:
    try:
        result = subprocess.run(["git", "status", "--short"], cwd=root, text=True, capture_output=True, check=False)
    except OSError:
        return []
    files: list[str] = []
    for line in result.stdout.splitlines():
        if len(line) >= 4:
            files.append(line[3:].strip().replace("\\", "/"))
    return files


def _parse_captured_output(request: CodexBridgeRequest, stdout: str, stderr: str) -> CodexParsedOutput:
    if request.json_mode:
        parsed = parse_jsonl_output(stdout)
        if parsed.events or parsed.failed_turns or parsed.errors:
            if parsed.usage is None:
                parsed.usage = extract_text_usage(stderr)
            return parsed
    return parse_text_output(stdout, stderr)


def _status_from_execution(exit_code: int | None, parsed: CodexParsedOutput) -> str:
    if exit_code != 0:
        return "failed"
    if parsed.failed_turns:
        return "failed"
    return "succeeded"


def _excerpt(value: str, limit: int = 1200) -> str:
    value = redact_secrets(value.strip())
    if len(value) <= limit:
        return value
    return value[:limit] + "...[truncated]"


def _write_audit_record(
    request: CodexBridgeRequest,
    result: CodexBridgeResult,
    recorder: LifecycleRecorder,
    root: Path,
    prompt_hash: str | None,
) -> str:
    audit = {
        "version": 1,
        "request_id": request.request_id,
        "work_package_id": request.work_package_id,
        "request_classification": request.classification,
        "provider": request.provider,
        "model": request.model,
        "profile_label": request.codex_home_profile,
        "sandbox_mode": request.sandbox,
        "allowed_paths": {
            "read": [_rel(_resolve(path, root), root) for path in request.allowed_read_paths],
            "write": [_rel(_resolve(path, root), root) for path in request.allowed_write_paths],
        },
        "prompt_hash": prompt_hash,
        "command_run": _redacted_command(result.command),
        "cwd": result.cwd,
        "exit_code": result.exit_code,
        "usage": result.usage,
        "result_summary": {
            "status": result.status,
            "final_message_excerpt": _excerpt(result.final_message or ""),
            "stdout_excerpt": _excerpt(result.stdout),
            "stderr_excerpt": _excerpt(result.stderr),
            "stdout_hash": result.stdout_hash,
            "stderr_hash": result.stderr_hash,
            "json_event_counts": result.parsed_output.event_counts,
        },
        "lifecycle_events_emitted": recorder.events,
        "lifecycle_events_path": _rel(recorder.paths["events"], root),
        "current_status_snapshot_path": result.status_snapshot_path,
        "changed_files": result.changed_files,
        "tests_run": result.tests_run,
        "known_limitations": result.known_limitations,
        "promotion_recommendation": result.promotion_recommendation,
    }
    recorder.paths["audit"].write_text(json.dumps(_redact_tree(audit), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return _rel(recorder.paths["audit"], root)


def run_codex_bridge_request(
    request: CodexBridgeRequest,
    *,
    root: str | Path | None = None,
    dry_run: bool = False,
    run_process: Callable[..., Any] | None = None,
) -> CodexBridgeResult:
    base = estate_root(root).resolve(strict=False)
    started_dt = _now_dt()
    recorder = LifecycleRecorder(request, base, started_dt)
    prompt_path = _resolve(request.prompt_source, base)
    prompt_hash = _hash_file(prompt_path)
    command = build_codex_command(request)
    redacted_command = _redacted_command(command)
    cwd = _resolve(request.cwd, base)

    recorder.emit("validation_started", state="Validation", summary="Codex Bridge request validation started.", validation_status="running")
    validation = validate_bridge_request(request, base)
    if not validation.accepted:
        recorder.emit(
            "validation_failed",
            state="Blocked",
            summary="Codex Bridge request failed boundary validation.",
            validation_status="failed",
            attention_required=True,
        )
        recorder.emit(
            "policy_denied",
            state="Blocked",
            summary="Codex Bridge request denied by policy: " + "; ".join(validation.errors),
            validation_status="failed",
            attention_required=True,
        )
        finished = _now_dt()
        parsed = CodexParsedOutput(mode="none", errors=[{"message": error} for error in validation.errors])
        result = CodexBridgeResult(
            request_id=request.request_id,
            status="policy_denied",
            started_at=_iso(started_dt),
            finished_at=_iso(finished),
            duration_seconds=round((finished - started_dt).total_seconds(), 3),
            command=redacted_command,
            cwd=str(cwd),
            provider=request.provider,
            model=request.model,
            profile_label=request.codex_home_profile,
            sandbox=request.sandbox,
            exit_code=None,
            stdout="",
            stderr="",
            stdout_hash=_hash_bytes(b""),
            stderr_hash=_hash_bytes(b""),
            parsed_output=parsed,
            usage=None,
            final_message=None,
            lifecycle_events=recorder.events,
            events_path=_rel(recorder.paths["events"], base),
            status_snapshot_path=recorder.status_path,
            audit_path=None,
            changed_files=_git_changed_files(base),
            tests_run=[],
            known_limitations=PRESERVED_KNOWN_LIMITATIONS,
            promotion_recommendation="blocked_by_boundary_policy",
            validation_errors=validation.errors,
        )
        result.audit_path = _write_audit_record(request, result, recorder, base, prompt_hash)
        return result

    recorder.emit("validation_passed", state="Validation", summary="Codex Bridge request passed boundary validation.", validation_status="passed")
    recorder.emit("job_accepted", state="Accepted", summary="Codex Bridge job accepted for local execution.", validation_status="passed")

    if dry_run:
        recorder.emit("result_returned", state="Reviewing", summary="Dry-run returned command and validation result without invoking Codex.", validation_status="passed")
        recorder.emit("execution_complete", state="Completed", summary="Dry-run completed without live Codex execution.", validation_status="passed")
        finished = _now_dt()
        parsed = CodexParsedOutput(mode="dry_run", final_message="Dry-run validation passed; Codex CLI was not invoked.")
        result = CodexBridgeResult(
            request_id=request.request_id,
            status="dry_run_validated",
            started_at=_iso(started_dt),
            finished_at=_iso(finished),
            duration_seconds=round((finished - started_dt).total_seconds(), 3),
            command=redacted_command,
            cwd=str(cwd),
            provider=request.provider,
            model=request.model,
            profile_label=request.codex_home_profile,
            sandbox=request.sandbox,
            exit_code=None,
            stdout="",
            stderr="",
            stdout_hash=_hash_bytes(b""),
            stderr_hash=_hash_bytes(b""),
            parsed_output=parsed,
            usage=None,
            final_message=parsed.final_message,
            lifecycle_events=recorder.events,
            events_path=_rel(recorder.paths["events"], base),
            status_snapshot_path=recorder.status_path,
            audit_path=None,
            changed_files=_git_changed_files(base),
            tests_run=[],
            known_limitations=PRESERVED_KNOWN_LIMITATIONS,
            promotion_recommendation="review_command_before_live_execution",
        )
        result.audit_path = _write_audit_record(request, result, recorder, base, prompt_hash)
        return result

    recorder.emit("execution_started", state="Running", summary="Codex CLI child process started.", validation_status="passed")
    process_runner = run_process or subprocess.run
    stdout_raw: bytes | str | None = b""
    stderr_raw: bytes | str | None = b""
    exit_code: int | None = None
    try:
        completed = process_runner(
            _execution_command(command),
            cwd=str(cwd),
            input=_read_prompt(prompt_path).encode("utf-8"),
            capture_output=True,
            check=False,
        )
        stdout_raw = getattr(completed, "stdout", b"")
        stderr_raw = getattr(completed, "stderr", b"")
        exit_code = getattr(completed, "returncode", None)
    except OSError as exc:
        stderr_raw = str(exc)
        exit_code = 1

    stdout = normalize_text(stdout_raw)
    stderr = normalize_text(stderr_raw)
    parsed = _parse_captured_output(request, stdout, stderr)
    status = _status_from_execution(exit_code, parsed)
    if parsed.final_message is not None:
        recorder.emit("result_returned", state="Reviewing", summary="Codex Bridge parsed a final assistant message.", validation_status="passed")
    else:
        recorder.emit("checkpoint_reached", state="Reviewing", summary="Codex Bridge captured process output for review.", validation_status="passed")

    final_event = "execution_complete" if status == "succeeded" else "execution_failed"
    recorder.emit(
        final_event,
        state="Completed" if status == "succeeded" else "Failed",
        summary="Codex CLI execution completed." if status == "succeeded" else "Codex CLI execution failed.",
        validation_status="passed",
        attention_required=status != "succeeded",
    )
    finished = _now_dt()
    result = CodexBridgeResult(
        request_id=request.request_id,
        status=status,
        started_at=_iso(started_dt),
        finished_at=_iso(finished),
        duration_seconds=round((finished - started_dt).total_seconds(), 3),
        command=redacted_command,
        cwd=str(cwd),
        provider=request.provider,
        model=request.model,
        profile_label=request.codex_home_profile,
        sandbox=request.sandbox,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        stdout_hash=_hash_bytes(stdout_raw),
        stderr_hash=_hash_bytes(stderr_raw),
        parsed_output=parsed,
        usage=parsed.usage,
        final_message=parsed.final_message,
        lifecycle_events=recorder.events,
        events_path=_rel(recorder.paths["events"], base),
        status_snapshot_path=recorder.status_path,
        audit_path=None,
        changed_files=_git_changed_files(base),
        tests_run=list(request.validation_commands),
        known_limitations=PRESERVED_KNOWN_LIMITATIONS,
        promotion_recommendation="human_review_required_before_promotion",
    )
    result.audit_path = _write_audit_record(request, result, recorder, base, prompt_hash)
    return result


def format_codex_bridge_result(result: CodexBridgeResult) -> str:
    lines = [
        "Codex Bridge Result",
        f"Request: {result.request_id}",
        f"Status: {result.status}",
        f"Provider: {result.provider}",
        f"Sandbox: {result.sandbox}",
        f"Exit code: {result.exit_code}",
        f"Events: {result.events_path}",
        f"Status snapshot: {result.status_snapshot_path}",
        f"Audit: {result.audit_path}",
    ]
    if result.final_message:
        lines.extend(["", "Final Message", result.final_message])
    if result.validation_errors:
        lines.extend(["", "Validation Errors"])
        lines.extend(f"- {error}" for error in result.validation_errors)
    return "\n".join(lines)
