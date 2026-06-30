import json
from datetime import datetime
from pathlib import Path

from estate.core.paths import ESTATE_ROOT
from estate.core.service_layer import alfred_capabilities, route_capability

RUNTIME_ALFRED_DIR = ESTATE_ROOT / "runtime" / "alfred"
RUNTIME_JOBS_DIR = RUNTIME_ALFRED_DIR / "jobs"


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
