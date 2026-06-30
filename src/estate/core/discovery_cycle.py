import json
import time
from datetime import datetime

from estate.core.paths import ESTATE_ROOT
from estate.core.discovery import observe_ai_environment, generate_discovery_report
from estate.core.discovery_catalog import load_discovery_catalog, summarize_discovery_catalog

METRICS_PATH = ESTATE_ROOT / "data" / "discovery" / "metrics.json"


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def run_discovery_cycle():
    started_at = _now()
    start = time.perf_counter()

    steps = []
    failures = []

    try:
        observed = observe_ai_environment()

        if isinstance(observed, tuple):
            observation = observed[0]
        else:
            observation = observed

        if not isinstance(observation, dict):
            raise TypeError(f"observation root is {type(observation).__name__}, expected dict")

        steps.append({"name": "observe", "ok": True, "detail": "observation written"})
    except Exception as exc:
        observation = {}
        failures.append(str(exc))
        steps.append({"name": "observe", "ok": False, "detail": str(exc)})

    try:
        catalog = load_discovery_catalog()
        catalog_summary = summarize_discovery_catalog(catalog)
        steps.append({"name": "catalog", "ok": True, "detail": f"{catalog_summary.get('total')} entities"})
    except Exception as exc:
        catalog = {"entities": []}
        catalog_summary = {}
        failures.append(str(exc))
        steps.append({"name": "catalog", "ok": False, "detail": str(exc)})

    try:
        report = generate_discovery_report()
        report_lines = len([line for line in report.splitlines() if line.strip()])
        steps.append({"name": "report", "ok": True, "detail": f"{report_lines} non-empty lines"})
    except Exception as exc:
        report = ""
        report_lines = 0
        failures.append(str(exc))
        steps.append({"name": "report", "ok": False, "detail": str(exc)})

    duration_seconds = round(time.perf_counter() - start, 3)

    ollama = observation.get("ollama", {}) or {}
    models = ollama.get("models", []) or []

    metrics = {
        "version": 1,
        "started_at": started_at,
        "finished_at": _now(),
        "duration_seconds": duration_seconds,
        "ok": not failures,
        "failures": failures,
        "steps": steps,
        "changed_since_previous": observation.get("changed_since_previous"),
        "ollama_running": ollama.get("running"),
        "ollama_models": len(models),
        "catalog_entities": catalog_summary.get("total", 0),
        "catalog_active": catalog_summary.get("active", 0),
        "catalog_inactive": catalog_summary.get("inactive", 0),
        "report_lines": report_lines,
    }

    previous = {}
    if METRICS_PATH.exists():
        try:
            previous = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        except Exception:
            previous = {}

    if metrics["ok"]:
        metrics["consecutive_successful_runs"] = int(previous.get("consecutive_successful_runs", 0)) + 1
    else:
        metrics["consecutive_successful_runs"] = 0

    _write_json(METRICS_PATH, metrics)

    return {
        "ok": metrics["ok"],
        "metrics": metrics,
        "observation": observation,
        "catalog_summary": catalog_summary,
    }


def format_discovery_cycle_report(result):
    metrics = result.get("metrics", {})
    steps = metrics.get("steps", [])

    lines = [
        "=========================================",
        "Estate Discovery Cycle",
        "=========================================",
    ]

    for step in steps:
        mark = "PASS" if step.get("ok") else "FAIL"
        lines.append(f"{mark} | {step.get('name')}")
        if step.get("detail"):
            lines.append(f"     {step.get('detail')}")

    lines.extend([
        "",
        f"Changed since previous: {metrics.get('changed_since_previous')}",
        f"Ollama running: {metrics.get('ollama_running')}",
        f"Ollama models: {metrics.get('ollama_models')}",
        f"Catalog entities: {metrics.get('catalog_entities')}",
        f"Catalog active: {metrics.get('catalog_active')}",
        f"Catalog inactive: {metrics.get('catalog_inactive')}",
        f"Duration seconds: {metrics.get('duration_seconds')}",
        f"Consecutive successful runs: {metrics.get('consecutive_successful_runs')}",
    ])

    return "\n".join(lines)
