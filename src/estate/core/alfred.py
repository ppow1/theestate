import json
from datetime import datetime
from pathlib import Path

from estate.core.paths import ESTATE_ROOT
from estate.core.service_layer import alfred_capabilities, route_capability

RUNTIME_ALFRED_DIR = ESTATE_ROOT / "runtime" / "alfred"
RUNTIME_JOBS_DIR = RUNTIME_ALFRED_DIR / "jobs"


EXECUTION_POLICIES = {
    "safe_text_executor": {
        "writes_files": False,
        "uses_network": False,
        "requires_confirmation": False,
    },
    "safe_code_executor": {
        "writes_files": False,
        "uses_network": False,
        "requires_confirmation": False,
    },
    "dry_run": {
        "writes_files": False,
        "uses_network": False,
        "requires_confirmation": False,
    },
}


INTENT_RULES = [
    {
        "intent": "generate_image",
        "keywords": ["image", "picture", "photo", "render", "comfy", "sdxl", "draw"],
        "capabilities": ["image.generate"],
    },
    {
        "intent": "transcribe_audio",
        "keywords": ["transcribe", "audio", "recording", "meeting", "whisper"],
        "capabilities": ["audio.transcribe"],
    },
    {
        "intent": "synthesize_speech",
        "keywords": ["tts", "voice", "speak", "speech", "narrate", "kokoro"],
        "capabilities": ["text.to_speech"],
    },
    {
        "intent": "code_assistance",
        "keywords": ["code", "debug", "repair", "implement", "review", "python"],
        "capabilities": ["code.write", "code.review"],
    },
    {
        "intent": "reasoning",
        "keywords": ["plan", "summarize", "reason", "think", "analyze"],
        "capabilities": ["plan", "reason"],
    },
]


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _safe_job_id():
    return "job_" + datetime.now().strftime("%Y%m%d_%H%M%S")


def infer_intents(goal):
    text = goal.lower()
    matches = []

    for rule in INTENT_RULES:
        score = sum(1 for keyword in rule["keywords"] if keyword in text)
        if score:
            matches.append({
                "intent": rule["intent"],
                "score": score,
                "capabilities": rule["capabilities"],
            })

    if not matches:
        matches.append({
            "intent": "general_assistance",
            "score": 0,
            "capabilities": ["reason", "plan"],
        })

    return sorted(matches, key=lambda item: item["score"], reverse=True)


def plan_goal(goal):
    capabilities_surface = alfred_capabilities()
    intents = infer_intents(goal)

    required_capabilities = []
    for intent in intents:
        for capability in intent.get("capabilities", []):
            if capability not in required_capabilities:
                required_capabilities.append(capability)

    routes = []
    missing = []

    for capability in required_capabilities:
        route = route_capability(capability)
        available = route.get("available", [])
        routes.append(route)

        if not available:
            missing.append(capability)

    steps = []
    for route in routes:
        capability = route["capability"]
        available = route.get("available", [])
        if available:
            service = available[0]
            steps.append({
                "capability": capability,
                "service": service["id"],
                "service_name": service["name"],
                "resident": service["resident"],
                "status": "ready",
            })
        else:
            steps.append({
                "capability": capability,
                "service": None,
                "service_name": None,
                "resident": None,
                "status": "blocked",
            })

    return {
        "version": 1,
        "created_at": _now(),
        "goal": goal,
        "intents": intents,
        "required_capabilities": required_capabilities,
        "steps": steps,
        "missing_capabilities": missing,
        "ready": not missing,
        "available_capabilities": capabilities_surface.get("capabilities", []),
    }


def create_job(goal):
    plan = plan_goal(goal)
    RUNTIME_JOBS_DIR.mkdir(parents=True, exist_ok=True)

    job = {
        "version": 1,
        "id": _safe_job_id(),
        "created_at": _now(),
        "goal": goal,
        "status": "ready" if plan["ready"] else "blocked",
        "plan": plan,
        "events": [
            {
                "timestamp": _now(),
                "event": "job_created",
                "detail": "Alfred job prepared from goal",
            }
        ],
    }

    path = RUNTIME_JOBS_DIR / f"{job['id']}.json"
    path.write_text(json.dumps(job, indent=2, sort_keys=True), encoding="utf-8")
    return job


def list_jobs():
    RUNTIME_JOBS_DIR.mkdir(parents=True, exist_ok=True)
    jobs = []

    for path in sorted(RUNTIME_JOBS_DIR.glob("job_*.json")):
        try:
            jobs.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue

    return {
        "version": 1,
        "jobs": jobs,
        "count": len(jobs),
    }


def format_plan(plan):
    lines = [
        "=========================================",
        "Alfred Plan",
        "=========================================",
        f"Goal: {plan.get('goal')}",
        f"Ready: {plan.get('ready')}",
        "",
        "Intents:",
    ]

    for intent in plan.get("intents", []):
        lines.append(f"- {intent['intent']} score={intent['score']} capabilities={', '.join(intent['capabilities'])}")

    lines.append("")
    lines.append("Steps:")

    for step in plan.get("steps", []):
        lines.append(f"- {step['status']} | {step['capability']} -> {step.get('service')}")
        if step.get("resident"):
            lines.append(f"     Resident: {step['resident']}")

    if plan.get("missing_capabilities"):
        lines.append("")
        lines.append("Missing:")
        for capability in plan["missing_capabilities"]:
            lines.append(f"- {capability}")

    return "\n".join(lines)


def format_job(job):
    lines = [
        "=========================================",
        "Alfred Job",
        "=========================================",
        f"Job: {job.get('id')}",
        f"Status: {job.get('status')}",
        f"Goal: {job.get('goal')}",
        "",
        "Plan:",
    ]

    for step in job.get("plan", {}).get("steps", []):
        lines.append(f"- {step['status']} | {step['capability']} -> {step.get('service')}")

    return "\n".join(lines)


def format_jobs(payload=None):
    payload = payload or list_jobs()

    lines = [
        "=========================================",
        "Alfred Jobs",
        "=========================================",
        f"Jobs: {payload.get('count')}",
        "",
    ]

    for job in payload.get("jobs", [])[-20:]:
        lines.append(f"{job.get('id')} | {job.get('status')} | {job.get('goal')}")

    return "\n".join(lines)



def _job_path(job_id):
    return RUNTIME_JOBS_DIR / f"{job_id}.json"


def load_job(job_id):
    path = _job_path(job_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_job(job):
    RUNTIME_JOBS_DIR.mkdir(parents=True, exist_ok=True)
    path = _job_path(job["id"])
    path.write_text(json.dumps(job, indent=2, sort_keys=True), encoding="utf-8")
    return path


def append_job_event(job, event, detail):
    job.setdefault("events", [])
    job["events"].append({
        "timestamp": _now(),
        "event": event,
        "detail": detail,
    })


def _safe_execute_step(step, goal):
    capability = step.get("capability")

    if capability in ["plan", "reason", "summarize"]:
        return {
            "ok": True,
            "capability": capability,
            "mode": "safe_text_executor",
            "result": {
                "summary": f"Prepared reasoning output for goal: {goal}",
                "next_action": "Use service routing to select an executable provider when full execution is enabled.",
            },
        }

    if capability.startswith("code."):
        return {
            "ok": True,
            "capability": capability,
            "mode": "safe_code_executor",
            "result": {
                "summary": f"Prepared code-assistance execution plan for goal: {goal}",
                "safety": "No filesystem writes performed by this executor.",
            },
        }

    return {
        "ok": True,
        "capability": capability,
        "mode": "dry_run",
        "result": {
            "summary": f"Execution for {capability} is not yet enabled; dry-run completed.",
        },
    }


def execute_job(job_id):
    job = load_job(job_id)
    if not job:
        return {
            "ok": False,
            "error": "job not found",
            "job_id": job_id,
        }

    if job.get("status") not in ["ready", "planned"]:
        return {
            "ok": False,
            "error": f"job status is {job.get('status')}",
            "job": job,
        }

    append_job_event(job, "job_started", "Alfred job execution started")
    job["status"] = "running"
    save_job(job)

    results = []
    ok = True

    for step in job.get("plan", {}).get("steps", []):
        append_job_event(job, "step_started", step.get("capability"))
        result = _safe_execute_step(step, job.get("goal", ""))
        results.append(result)
        if result.get("ok"):
            append_job_event(job, "step_completed", step.get("capability"))
        else:
            ok = False
            append_job_event(job, "step_failed", step.get("capability"))

    job["results"] = results
    job["status"] = "completed" if ok else "failed"
    append_job_event(job, "job_completed" if ok else "job_failed", job["status"])
    save_job(job)
    write_job_artifacts(job)

    return {
        "ok": ok,
        "job": job,
        "results": results,
        "artifacts": job.get("artifacts", {}),
    }


def format_execution_result(result):
    if not result.get("ok"):
        return f"Alfred execution failed: {result.get('error')}"

    job = result.get("job", {})
    lines = [
        "=========================================",
        "Alfred Execution Result",
        "=========================================",
        f"Job: {job.get('id')}",
        f"Status: {job.get('status')}",
        f"Goal: {job.get('goal')}",
        "",
        "Results:",
    ]

    for item in result.get("results", []):
        lines.append(f"- {item.get('mode')} | {item.get('capability')} | ok={item.get('ok')}")
        summary = item.get("result", {}).get("summary")
        if summary:
            lines.append(f"     {summary}")

    return "\n".join(lines)



def get_execution_policy(mode=None):
    if mode:
        return EXECUTION_POLICIES.get(mode, {})
    return EXECUTION_POLICIES


def inspect_job(job_id):
    job = load_job(job_id)
    if not job:
        return {
            "ok": False,
            "error": "job not found",
            "job_id": job_id,
        }

    return {
        "ok": True,
        "job": job,
        "events": job.get("events", []),
        "status": job.get("status"),
        "results": job.get("results", []),
    }


def cancel_job(job_id):
    job = load_job(job_id)
    if not job:
        return {
            "ok": False,
            "error": "job not found",
            "job_id": job_id,
        }

    if job.get("status") in ["completed", "failed", "cancelled"]:
        return {
            "ok": False,
            "error": f"cannot cancel job with status {job.get('status')}",
            "job": job,
        }

    job["status"] = "cancelled"
    append_job_event(job, "job_cancelled", "Job cancelled by command")
    save_job(job)

    return {
        "ok": True,
        "job": job,
    }


def retry_job(job_id):
    job = load_job(job_id)
    if not job:
        return {
            "ok": False,
            "error": "job not found",
            "job_id": job_id,
        }

    retry = create_job(job.get("goal", ""))
    retry["parent_job_id"] = job.get("id")
    append_job_event(retry, "job_retry_created", f"Retry of {job.get('id')}")
    save_job(retry)

    return {
        "ok": True,
        "job": retry,
        "parent_job": job,
    }


def format_job_inspection(result):
    if not result.get("ok"):
        return f"Alfred job inspection failed: {result.get('error')}"

    job = result.get("job", {})
    lines = [
        "=========================================",
        "Alfred Job Inspection",
        "=========================================",
        f"Job: {job.get('id')}",
        f"Status: {job.get('status')}",
        f"Goal: {job.get('goal')}",
        "",
        "Events:",
    ]

    for event in result.get("events", []):
        lines.append(f"- {event.get('timestamp')} | {event.get('event')} | {event.get('detail')}")

    lines.append("")
    lines.append("Results:")

    for item in result.get("results", []):
        lines.append(f"- {item.get('mode')} | {item.get('capability')} | ok={item.get('ok')}")

    return "\n".join(lines)


def format_execution_policy(policy=None):
    policy = policy or get_execution_policy()
    lines = [
        "=========================================",
        "Alfred Execution Policy",
        "=========================================",
    ]

    for mode, data in sorted(policy.items()):
        lines.append(f"{mode}:")
        for key, value in sorted(data.items()):
            lines.append(f"  {key}: {value}")

    return "\n".join(lines)



def _job_artifact_dir(job_id):
    return RUNTIME_JOBS_DIR / job_id


def write_job_artifacts(job):
    artifact_dir = _job_artifact_dir(job["id"])
    artifact_dir.mkdir(parents=True, exist_ok=True)

    result_path = artifact_dir / "result.json"
    events_path = artifact_dir / "events.json"
    summary_path = artifact_dir / "summary.txt"

    result_payload = {
        "job_id": job.get("id"),
        "status": job.get("status"),
        "goal": job.get("goal"),
        "results": job.get("results", []),
    }

    result_path.write_text(json.dumps(result_payload, indent=2, sort_keys=True), encoding="utf-8")
    events_path.write_text(json.dumps(job.get("events", []), indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "Alfred Job Result",
        "=================",
        f"Job: {job.get('id')}",
        f"Status: {job.get('status')}",
        f"Goal: {job.get('goal')}",
        "",
        "Results:",
    ]

    for item in job.get("results", []):
        lines.append(f"- {item.get('capability')} via {item.get('mode')}: ok={item.get('ok')}")
        summary = item.get("result", {}).get("summary")
        if summary:
            lines.append(f"  {summary}")

    summary_path.write_text("\n".join(lines), encoding="utf-8")

    job["artifacts"] = {
        "dir": str(artifact_dir),
        "result": str(result_path),
        "events": str(events_path),
        "summary": str(summary_path),
    }

    save_job(job)
    return job["artifacts"]


def get_job_result(job_id):
    job = load_job(job_id)
    if not job:
        return {
            "ok": False,
            "error": "job not found",
            "job_id": job_id,
        }

    artifacts = job.get("artifacts") or {}
    summary = None
    summary_path = artifacts.get("summary")
    if summary_path and Path(summary_path).exists():
        summary = Path(summary_path).read_text(encoding="utf-8")

    return {
        "ok": True,
        "job_id": job_id,
        "status": job.get("status"),
        "goal": job.get("goal"),
        "artifacts": artifacts,
        "summary": summary,
        "results": job.get("results", []),
    }


def format_job_result(result):
    if not result.get("ok"):
        return f"Alfred job result failed: {result.get('error')}"

    if result.get("summary"):
        return result["summary"]

    return format_job_inspection({
        "ok": True,
        "job": {
            "id": result.get("job_id"),
            "status": result.get("status"),
            "goal": result.get("goal"),
            "results": result.get("results", []),
        },
        "events": [],
        "results": result.get("results", []),
    })
