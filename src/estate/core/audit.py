import json
import re
import subprocess
import time
from pathlib import Path
from estate.core.paths import ESTATE_ROOT, LEDGER_PATH, DEVLOG_PATH

def _run(cmd):
    try:
        result = subprocess.run(cmd, cwd=str(ESTATE_ROOT), capture_output=True, text=True, shell=True)
        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }
    except Exception as e:
        return {
            "ok": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e)
        }

def _latest_ec_from_text(text):
    matches = re.findall(r"EC-\d{6}", text)
    return matches[-1] if matches else None

def _latest_git_ec():
    result = _run("git log -1 --pretty=%s")
    if not result["ok"]:
        return None, result
    return _latest_ec_from_text(result["stdout"]), result

def _latest_ledger_ec():
    text = LEDGER_PATH.read_text(encoding="utf-8") if LEDGER_PATH.exists() else ""
    return _latest_ec_from_text(text)

def _json_ok(path):
    try:
        json.loads(Path(path).read_text(encoding="utf-8"))
        return True, ""
    except Exception as e:
        return False, str(e)


def _required_paths_check():
    required = [
        "data/registry/residents.json",
        "data/registry/services.json",
        "data/registry/capabilities.json",
        "data/registry/providers.json",
        "estate_ledger/ledger.md",
        "development/devlog.md",
        "estate.bat",
        "runtime/discovery",
    ]
    missing = [path for path in required if not (ESTATE_ROOT / path).exists()]
    return {
        "name": "estate:required_paths",
        "ok": not missing,
        "detail": f"{len(required)} present" if not missing else ", ".join(missing),
    }

def _registry_shape_check(path, collection_key):
    full_path = ESTATE_ROOT / path
    try:
        data = json.loads(full_path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"name": f"registry_shape:{path}", "ok": False, "detail": str(e)}

    if isinstance(data, list):
        items = data
        shape = "list"
    elif isinstance(data, dict):
        if collection_key in data:
            items = data[collection_key]
            shape = f"object.{collection_key}"
        elif "items" in data:
            items = data["items"]
            shape = "object.items"
        else:
            return {
                "name": f"registry_shape:{path}",
                "ok": False,
                "detail": f"object missing {collection_key} or items collection",
            }
    else:
        return {"name": f"registry_shape:{path}", "ok": False, "detail": "registry root is not a list or object"}

    if not isinstance(items, list):
        return {"name": f"registry_shape:{path}", "ok": False, "detail": "registry collection is not a list"}

    seen = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            return {"name": f"registry_shape:{path}", "ok": False, "detail": f"item[{index}] is not an object"}
        item_id = item.get("id")
        if not item_id:
            return {"name": f"registry_shape:{path}", "ok": False, "detail": f"item[{index}] missing id"}
        if item_id in seen:
            return {"name": f"registry_shape:{path}", "ok": False, "detail": f"duplicate id: {item_id}"}
        seen.add(item_id)

    return {"name": f"registry_shape:{path}", "ok": True, "detail": f"{len(items)} records ({shape})"}


def _observation_history_check():
    observations = ESTATE_ROOT / "observations"
    latest = ESTATE_ROOT / "runtime" / "discovery" / "ai_environment_latest.json"
    history = [
        path for path in observations.glob("ai_environment_*.json")
        if not path.name.endswith("_latest.json")
    ]
    if not latest.exists():
        return {"name": "observations:latest_present", "ok": False, "detail": "missing latest observation"}
    if not history:
        return {"name": "observations:history_present", "ok": False, "detail": "no timestamped observation history"}
    return {"name": "observations:history_present", "ok": True, "detail": f"{len(history)} historical observations"}

def _latest_ledger_ec_in_devlog_check():
    ledger = LEDGER_PATH.read_text(encoding="utf-8", errors="replace") if LEDGER_PATH.exists() else ""
    devlog = DEVLOG_PATH.read_text(encoding="utf-8", errors="replace") if DEVLOG_PATH.exists() else ""
    latest = _latest_ec_from_text(ledger)
    if not latest:
        return {"name": "history:latest_ledger_ec_in_devlog", "ok": False, "detail": "no Estate Change found in ledger"}
    return {
        "name": "history:latest_ledger_ec_in_devlog",
        "ok": latest in devlog,
        "detail": latest if latest in devlog else f"{latest} missing from devlog",
    }



def _audit_check_severity(name):
    if name.startswith("git:"):
        return "error"
    if name.startswith("history:"):
        return "error"
    if name.startswith("syntax:"):
        return "error"
    if name.startswith("runtime:"):
        return "error"
    if name.startswith("json:"):
        return "error"
    return "error"


def _enrich_checks(checks, group_name):
    enriched = []
    for check in checks:
        item = dict(check)
        item.setdefault("group", group_name)
        item.setdefault("severity", _audit_check_severity(item.get("name", "")))
        item.setdefault("duration_ms", 0)
        enriched.append(item)
    return enriched


def _run_check_group(group_name, func):
    start = time.perf_counter()
    checks = func()
    duration_ms = round((time.perf_counter() - start) * 1000, 3)
    enriched = _enrich_checks(checks, group_name)
    for check in enriched:
        check["group_duration_ms"] = duration_ms
    return enriched


def _syntax_checks():
    checks = []
    py_files = [
        "src/estate/cli/main.py",
        "src/estate/core/discovery.py",
        "src/estate/core/provider_sync.py",
        "src/estate/core/discovery_catalog.py",
        "src/estate/core/discovery_cycle.py",
        "src/estate/core/discovery_service.py",
        "src/estate/core/discovery_runtime.py",
        "src/estate/core/audit_runtime.py",
        "src/estate/core/service_layer.py",
        "src/estate/core/alfred.py",
    ]

    for file in py_files:
        result = _run(f"python -m py_compile {file}")
        checks.append({
            "name": f"syntax:{file}",
            "ok": result["ok"],
            "detail": result["stderr"] or result["stdout"],
        })

    return checks


def _runtime_checks():
    checks = []
    for command in [".\\estate.bat status", ".\\estate.bat discovery-report"]:
        result = _run(command)
        detail = result["stderr"] or result["stdout"].splitlines()[0] if result["stdout"] else ""
        checks.append({
            "name": f"runtime:{command}",
            "ok": result["ok"],
            "detail": detail,
        })

    checks.append(_cli_inventory_check())
    checks.append(_audit_runtime_artifact_check())
    checks.append(_audit_summary_command_check())
    checks.append(_service_readiness_command_check())
    checks.append(_service_status_command_check())
    checks.append(_service_route_command_check())
    checks.append(_alfred_capabilities_command_check())
    checks.append(_alfred_cleanup_command_check())
    checks.append(_alfred_briefing_command_check())
    checks.append(_alfred_request_queue_command_check())
    checks.append(_alfred_status_command_check())
    checks.append(_alfred_task_command_check())
    checks.append(_alfred_local_reasoning_executor_check())
    checks.append(_alfred_code_review_executor_check())
    checks.append(_alfred_plan_command_check())
    checks.append(_alfred_run_command_check())
    checks.append(_alfred_jobs_command_check())
    checks.append(_alfred_execute_command_check())
    checks.append(_alfred_result_command_check())
    checks.append(_alfred_result_command_check())
    checks.append(_alfred_policy_command_check())
    checks.append(_alfred_job_control_command_check())

    return checks



def _cli_inventory_check():
    result = _run(".\\estate.bat --help")
    required = [
        "status",
        "list",
        "services",
        "capabilities",
        "providers",
        "discover",
        "discover-ai",
        "discovery-report",
        "discovery-status",
        "discovery-catalog",
        "discovery-refresh",
        "sync-ollama",
        "audit",
        "audit-summary",
        "service-readiness",
        "service-status",
        "service-route",
        "alfred-capabilities",
        "alfred-cleanup",
        "alfred-briefing",
        "alfred-request",
        "alfred-requests",
        "alfred-promote",
        "alfred-status",
        "alfred-task",
        "alfred-plan",
        "alfred-run",
        "alfred-jobs",
        "alfred-execute",
        "alfred-result",
        "alfred-result",
        "alfred-inspect",
        "alfred-cancel",
        "alfred-retry",
        "alfred-policy",
    ]

    if not result["ok"]:
        return {
            "name": "runtime:cli_inventory",
            "ok": False,
            "detail": result["stderr"] or result["stdout"],
        }

    missing = [command for command in required if command not in result["stdout"]]
    return {
        "name": "runtime:cli_inventory",
        "ok": not missing,
        "detail": f"{len(required)} commands present" if not missing else "missing: " + ", ".join(missing),
    }



def _audit_runtime_artifact_check():
    path = ESTATE_ROOT / "runtime" / "audit" / "latest.json"
    if not path.exists():
        return {
            "name": "runtime:audit_latest_artifact",
            "ok": False,
            "detail": "missing runtime/audit/latest.json",
        }

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {
            "name": "runtime:audit_latest_artifact",
            "ok": False,
            "detail": str(e),
        }

    report = data.get("report", {})
    checks = report.get("checks", [])

    if not isinstance(checks, list):
        return {
            "name": "runtime:audit_latest_artifact",
            "ok": False,
            "detail": "report checks is not a list",
        }

    missing = []
    for index, check in enumerate(checks):
        for field in ["name", "ok", "detail", "group", "severity", "duration_ms", "group_duration_ms"]:
            if field not in check:
                missing.append(f"checks[{index}].{field}")

    return {
        "name": "runtime:audit_latest_artifact",
        "ok": not missing,
        "detail": f"{len(checks)} enriched checks" if not missing else "missing: " + ", ".join(missing[:5]),
    }



def _audit_summary_command_check():
    result = _run(".\\estate.bat audit-summary --json")
    if not result["ok"]:
        return {
            "name": "runtime:audit_summary_json",
            "ok": False,
            "detail": result["stderr"] or result["stdout"],
        }

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {
            "name": "runtime:audit_summary_json",
            "ok": False,
            "detail": str(e),
        }

    required = ["exists", "passed", "failed", "groups", "severities"]
    missing = [key for key in required if key not in data]

    return {
        "name": "runtime:audit_summary_json",
        "ok": not missing and data.get("exists") is True,
        "detail": "summary valid" if not missing else "missing: " + ", ".join(missing),
    }



def _service_status_command_check():
    result = _run(".\\estate.bat service-status --json")
    if not result["ok"]:
        return {
            "name": "runtime:service_status_json",
            "ok": False,
            "detail": result["stderr"] or result["stdout"],
        }

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {
            "name": "runtime:service_status_json",
            "ok": False,
            "detail": str(e),
        }

    services = data.get("services", [])
    if not isinstance(services, list) or not services:
        return {
            "name": "runtime:service_status_json",
            "ok": False,
            "detail": "no services",
        }

    missing = []
    for index, service in enumerate(services):
        for field in ["id", "name", "resident", "capabilities", "providers", "requirements", "available", "alfred_use"]:
            if field not in service:
                missing.append(f"services[{index}].{field}")

    return {
        "name": "runtime:service_status_json",
        "ok": not missing,
        "detail": f"{len(services)} services" if not missing else "missing: " + ", ".join(missing[:5]),
    }


def _service_route_command_check():
    result = _run(".\\estate.bat service-route image.generate --json")
    if not result["ok"]:
        return {
            "name": "runtime:service_route_json",
            "ok": False,
            "detail": result["stderr"] or result["stdout"],
        }

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {
            "name": "runtime:service_route_json",
            "ok": False,
            "detail": str(e),
        }

    return {
        "name": "runtime:service_route_json",
        "ok": data.get("capability") == "image.generate" and isinstance(data.get("matches"), list),
        "detail": f"{len(data.get('matches', []))} matches",
    }


def _alfred_capabilities_command_check():
    result = _run(".\\estate.bat alfred-capabilities --json")
    if not result["ok"]:
        return {
            "name": "runtime:alfred_capabilities_json",
            "ok": False,
            "detail": result["stderr"] or result["stdout"],
        }

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {
            "name": "runtime:alfred_capabilities_json",
            "ok": False,
            "detail": str(e),
        }

    capabilities = data.get("capabilities", [])
    return {
        "name": "runtime:alfred_capabilities_json",
        "ok": isinstance(capabilities, list) and len(capabilities) > 0,
        "detail": f"{len(capabilities)} capabilities",
    }



def _alfred_plan_command_check():
    result = _run('.\\estate.bat alfred-plan "generate an image of the estate" --json')
    if not result["ok"]:
        return {
            "name": "runtime:alfred_plan_json",
            "ok": False,
            "detail": result["stderr"] or result["stdout"],
        }

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {
            "name": "runtime:alfred_plan_json",
            "ok": False,
            "detail": str(e),
        }

    required = ["goal", "intents", "required_capabilities", "steps", "ready"]
    missing = [key for key in required if key not in data]

    return {
        "name": "runtime:alfred_plan_json",
        "ok": not missing and data.get("ready") is True,
        "detail": "plan valid" if not missing else "missing: " + ", ".join(missing),
    }


def _alfred_run_command_check():
    result = _run('.\\estate.bat alfred-run "summarize and plan work" --json')
    if not result["ok"]:
        return {
            "name": "runtime:alfred_run_json",
            "ok": False,
            "detail": result["stderr"] or result["stdout"],
        }

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {
            "name": "runtime:alfred_run_json",
            "ok": False,
            "detail": str(e),
        }

    required = ["id", "goal", "status", "plan", "events"]
    missing = [key for key in required if key not in data]

    return {
        "name": "runtime:alfred_run_json",
        "ok": not missing and data.get("status") == "ready",
        "detail": data.get("id", "job valid") if not missing else "missing: " + ", ".join(missing),
    }


def _alfred_jobs_command_check():
    result = _run(".\\estate.bat alfred-jobs --json")
    if not result["ok"]:
        return {
            "name": "runtime:alfred_jobs_json",
            "ok": False,
            "detail": result["stderr"] or result["stdout"],
        }

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {
            "name": "runtime:alfred_jobs_json",
            "ok": False,
            "detail": str(e),
        }

    return {
        "name": "runtime:alfred_jobs_json",
        "ok": isinstance(data.get("jobs"), list),
        "detail": f"{len(data.get('jobs', []))} jobs",
    }



def _alfred_execute_command_check():
    create_result = _run('.\\estate.bat alfred-run "summarize and plan work" --json')
    if not create_result["ok"]:
        return {
            "name": "runtime:alfred_execute_json",
            "ok": False,
            "detail": create_result["stderr"] or create_result["stdout"],
        }

    try:
        created = json.loads(create_result["stdout"])
    except Exception as e:
        return {
            "name": "runtime:alfred_execute_json",
            "ok": False,
            "detail": str(e),
        }

    job_id = created.get("id")
    if not job_id:
        return {
            "name": "runtime:alfred_execute_json",
            "ok": False,
            "detail": "created job missing id",
        }

    result = _run(f'.\\estate.bat alfred-execute {job_id} --json')
    if not result["ok"]:
        return {
            "name": "runtime:alfred_execute_json",
            "ok": False,
            "detail": result["stderr"] or result["stdout"],
        }

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {
            "name": "runtime:alfred_execute_json",
            "ok": False,
            "detail": str(e),
        }

    job = data.get("job", {})
    return {
        "name": "runtime:alfred_execute_json",
        "ok": data.get("ok") is True and job.get("status") == "completed",
        "detail": job.get("id", "execution valid"),
    }



def _alfred_policy_command_check():
    result = _run(".\\estate.bat alfred-policy --json")
    if not result["ok"]:
        return {
            "name": "runtime:alfred_policy_json",
            "ok": False,
            "detail": result["stderr"] or result["stdout"],
        }

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {
            "name": "runtime:alfred_policy_json",
            "ok": False,
            "detail": str(e),
        }

    return {
        "name": "runtime:alfred_policy_json",
        "ok": "safe_text_executor" in data and "dry_run" in data,
        "detail": f"{len(data.keys())} policies",
    }


def _alfred_job_control_command_check():
    create_result = _run('.\\estate.bat alfred-run "plan a safe code review" --json')
    if not create_result["ok"]:
        return {
            "name": "runtime:alfred_job_control_json",
            "ok": False,
            "detail": create_result["stderr"] or create_result["stdout"],
        }

    try:
        created = json.loads(create_result["stdout"])
    except Exception as e:
        return {
            "name": "runtime:alfred_job_control_json",
            "ok": False,
            "detail": str(e),
        }

    job_id = created.get("id")
    inspect_result = _run(f'.\\estate.bat alfred-inspect {job_id} --json')
    retry_result = _run(f'.\\estate.bat alfred-retry {job_id} --json')

    if not inspect_result["ok"]:
        return {
            "name": "runtime:alfred_job_control_json",
            "ok": False,
            "detail": inspect_result["stderr"] or inspect_result["stdout"],
        }

    if not retry_result["ok"]:
        return {
            "name": "runtime:alfred_job_control_json",
            "ok": False,
            "detail": retry_result["stderr"] or retry_result["stdout"],
        }

    try:
        inspected = json.loads(inspect_result["stdout"])
        retry = json.loads(retry_result["stdout"])
    except Exception as e:
        return {
            "name": "runtime:alfred_job_control_json",
            "ok": False,
            "detail": str(e),
        }

    return {
        "name": "runtime:alfred_job_control_json",
        "ok": inspected.get("ok") is True and retry.get("ok") is True,
        "detail": f"inspected={job_id}",
    }



def _alfred_result_command_check():
    create_result = _run('.\\estate.bat alfred-run "summarize and plan work" --json')
    if not create_result["ok"]:
        return {
            "name": "runtime:alfred_result_json",
            "ok": False,
            "detail": create_result["stderr"] or create_result["stdout"],
        }

    try:
        created = json.loads(create_result["stdout"])
    except Exception as e:
        return {
            "name": "runtime:alfred_result_json",
            "ok": False,
            "detail": str(e),
        }

    job_id = created.get("id")
    execute_result = _run(f'.\\estate.bat alfred-execute {job_id} --json')
    if not execute_result["ok"]:
        return {
            "name": "runtime:alfred_result_json",
            "ok": False,
            "detail": execute_result["stderr"] or execute_result["stdout"],
        }

    result = _run(f'.\\estate.bat alfred-result {job_id} --json')
    if not result["ok"]:
        return {
            "name": "runtime:alfred_result_json",
            "ok": False,
            "detail": result["stderr"] or result["stdout"],
        }

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {
            "name": "runtime:alfred_result_json",
            "ok": False,
            "detail": str(e),
        }

    artifacts = data.get("artifacts", {})
    return {
        "name": "runtime:alfred_result_json",
        "ok": data.get("ok") is True and bool(artifacts.get("summary")),
        "detail": artifacts.get("summary", "result valid"),
    }



def _alfred_task_command_check():
    result = _run('.\\estate.bat alfred-task "summarize what the Estate can currently do" --json')
    if not result["ok"]:
        return {"name": "runtime:alfred_task_json", "ok": False, "detail": result["stderr"] or result["stdout"]}

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {"name": "runtime:alfred_task_json", "ok": False, "detail": str(e)}

    return {
        "name": "runtime:alfred_task_json",
        "ok": data.get("ok") is True and bool(data.get("job_id")),
        "detail": data.get("job_id", "task valid"),
    }



def _alfred_status_command_check():
    result = _run(".\\estate.bat alfred-status --json")
    if not result["ok"]:
        return {"name": "runtime:alfred_status_json", "ok": False, "detail": result["stderr"] or result["stdout"]}

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {"name": "runtime:alfred_status_json", "ok": False, "detail": str(e)}

    return {
        "name": "runtime:alfred_status_json",
        "ok": data.get("operator_summary", {}).get("ready") is True,
        "detail": data.get("operator_summary", {}).get("message", "status valid"),
    }



def _alfred_request_queue_command_check():
    created = _run('.\\estate.bat alfred-request "prepare an operator summary" --json')
    if not created["ok"]:
        return {"name": "runtime:alfred_request_queue_json", "ok": False, "detail": created["stderr"] or created["stdout"]}

    try:
        request = json.loads(created["stdout"])
    except Exception as e:
        return {"name": "runtime:alfred_request_queue_json", "ok": False, "detail": str(e)}

    request_id = request.get("id")
    listed = _run(".\\estate.bat alfred-requests --json")
    promoted = _run(f".\\estate.bat alfred-promote {request_id} --json")

    if not listed["ok"]:
        return {"name": "runtime:alfred_request_queue_json", "ok": False, "detail": listed["stderr"] or listed["stdout"]}
    if not promoted["ok"]:
        return {"name": "runtime:alfred_request_queue_json", "ok": False, "detail": promoted["stderr"] or promoted["stdout"]}

    try:
        promotion = json.loads(promoted["stdout"])
    except Exception as e:
        return {"name": "runtime:alfred_request_queue_json", "ok": False, "detail": str(e)}

    return {
        "name": "runtime:alfred_request_queue_json",
        "ok": promotion.get("ok") is True and promotion.get("job", {}).get("id"),
        "detail": request_id,
    }



def _alfred_briefing_command_check():
    result = _run(".\\estate.bat alfred-briefing --json")
    if not result["ok"]:
        return {"name": "runtime:alfred_briefing_json", "ok": False, "detail": result["stderr"] or result["stdout"]}

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {"name": "runtime:alfred_briefing_json", "ok": False, "detail": str(e)}

    summary = data.get("summary", {})
    return {
        "name": "runtime:alfred_briefing_json",
        "ok": summary.get("ready") is True and "latest_jobs" in data,
        "detail": f"jobs={summary.get('jobs')} requests={summary.get('queued_requests')}",
    }



def _alfred_cleanup_command_check():
    result = _run(".\\estate.bat alfred-cleanup --keep 500 --json")
    if not result["ok"]:
        return {"name": "runtime:alfred_cleanup_json", "ok": False, "detail": result["stderr"] or result["stdout"]}

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {"name": "runtime:alfred_cleanup_json", "ok": False, "detail": str(e)}

    return {
        "name": "runtime:alfred_cleanup_json",
        "ok": data.get("ok") is True and "removed_count" in data,
        "detail": f"removed={data.get('removed_count')}",
    }



def _service_readiness_command_check():
    result = _run(".\\estate.bat service-readiness --json")
    if not result["ok"]:
        return {"name": "runtime:service_readiness_json", "ok": False, "detail": result["stderr"] or result["stdout"]}

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {"name": "runtime:service_readiness_json", "ok": False, "detail": str(e)}

    return {
        "name": "runtime:service_readiness_json",
        "ok": "ready_count" in data and "blocked_count" in data,
        "detail": f"ready={data.get('ready_count')} blocked={data.get('blocked_count')}",
    }



def _alfred_local_reasoning_executor_check():
    result = _run('.\\estate.bat alfred-task "reason about the current Estate readiness" --json')
    if not result["ok"]:
        return {"name": "runtime:alfred_local_reasoning_json", "ok": False, "detail": result["stderr"] or result["stdout"]}

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {"name": "runtime:alfred_local_reasoning_json", "ok": False, "detail": str(e)}

    text = data.get("result", {}).get("summary") or ""
    return {
        "name": "runtime:alfred_local_reasoning_json",
        "ok": data.get("ok") is True and "Local Reasoning Result" in text,
        "detail": data.get("job_id", "local reasoning valid"),
    }



def _alfred_code_review_executor_check():
    result = _run('.\\estate.bat alfred-task "review code safely" --json')
    if not result["ok"]:
        return {"name": "runtime:alfred_code_review_json", "ok": False, "detail": result["stderr"] or result["stdout"]}

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {"name": "runtime:alfred_code_review_json", "ok": False, "detail": str(e)}

    text = data.get("result", {}).get("summary") or ""
    return {
        "name": "runtime:alfred_code_review_json",
        "ok": data.get("ok") is True and "Safe Code Review Result" in text,
        "detail": data.get("job_id", "code review valid"),
    }


def _json_checks():
    checks = []
    for path in [
        "data/registry/residents.json",
        "data/registry/services.json",
        "data/registry/capabilities.json",
        "data/registry/providers.json",
    ]:
        ok, detail = _json_ok(ESTATE_ROOT / path)
        checks.append({
            "name": f"json:{path}",
            "ok": ok,
            "detail": detail,
        })

    return checks


def _registry_checks():
    checks = [_required_paths_check()]

    for path, collection_key in [
        ("data/registry/residents.json", "residents"),
        ("data/registry/services.json", "services"),
        ("data/registry/capabilities.json", "capabilities"),
        ("data/registry/providers.json", "providers"),
    ]:
        checks.append(_registry_shape_check(path, collection_key))

    return checks


def _observation_checks():
    return [
        _observation_history_check(),
        _observation_latest_shape_check(),
        _observation_history_json_check(),
        _discovery_report_contract_check(),
        _discovery_json_command_check(),
        _discovery_status_command_check(),
        _discovery_catalog_schema_check(),
        _discovery_catalog_command_check(),
        _discovery_catalog_latest_coverage_check(),
        _discovery_cycle_command_check(),
        _discovery_metrics_file_check(),
        _discovery_refresh_command_check(),
    ]




def _devlog_structure_check():
    text = DEVLOG_PATH.read_text(encoding="utf-8", errors="replace") if DEVLOG_PATH.exists() else ""
    entries = re.findall(r"^EC-\d{6} - .*$", text, flags=re.MULTILINE)

    if not entries:
        return {
            "name": "history:devlog_structure",
            "ok": False,
            "detail": "no devlog EC entries found",
        }

    ec_ids = [re.search(r"(EC-\d{6})", entry).group(1) for entry in entries]
    duplicates = sorted({ec_id for ec_id in ec_ids if ec_ids.count(ec_id) > 1})

    if duplicates:
        return {
            "name": "history:devlog_structure",
            "ok": False,
            "detail": "duplicate entries: " + ", ".join(duplicates),
        }

    latest_ledger = _latest_ledger_ec()
    latest_devlog = ec_ids[-1] if ec_ids else None

    if latest_ledger != latest_devlog:
        return {
            "name": "history:devlog_structure",
            "ok": False,
            "detail": f"ledger={latest_ledger} devlog={latest_devlog}",
        }

    return {
        "name": "history:devlog_structure",
        "ok": True,
        "detail": f"{len(ec_ids)} EC entries; latest={latest_devlog}",
    }


def _ledger_structure_check():
    text = LEDGER_PATH.read_text(encoding="utf-8", errors="replace") if LEDGER_PATH.exists() else ""
    entries = re.findall(r"^## (EC-\d{6}) - .*$", text, flags=re.MULTILINE)

    if not entries:
        return {
            "name": "history:ledger_structure",
            "ok": False,
            "detail": "no EC ledger entries found",
        }

    numbers = [int(entry.split("-")[1]) for entry in entries]
    duplicates = sorted({entry for entry in entries if entries.count(entry) > 1})

    if duplicates:
        return {
            "name": "history:ledger_structure",
            "ok": False,
            "detail": "duplicate entries: " + ", ".join(duplicates),
        }

    gaps = []
    for previous, current in zip(numbers, numbers[1:]):
        if current != previous + 1:
            gaps.append(f"EC-{previous:06d}->EC-{current:06d}")

    if gaps:
        return {
            "name": "history:ledger_structure",
            "ok": False,
            "detail": "sequence gaps: " + ", ".join(gaps),
        }

    required_fields = ["Timestamp:", "Location:", "Status:", "Classification:", "Summary:"]
    missing = []
    blocks = re.split(r"(?=^## EC-\d{6} - )", text, flags=re.MULTILINE)

    for block in blocks:
        match = re.search(r"^## (EC-\d{6}) - ", block, flags=re.MULTILINE)
        if not match:
            continue
        ec_id = match.group(1)
        for field in required_fields:
            if field not in block:
                missing.append(f"{ec_id}:{field.rstrip(':')}")

    if missing:
        return {
            "name": "history:ledger_structure",
            "ok": False,
            "detail": "missing fields: " + ", ".join(missing[:8]),
        }

    return {
        "name": "history:ledger_structure",
        "ok": True,
        "detail": f"{len(entries)} sequential entries",
    }



def _observation_latest_shape_check():
    path = ESTATE_ROOT / "runtime" / "discovery" / "ai_environment_latest.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {
            "name": "observations:latest_shape",
            "ok": False,
            "detail": str(e),
        }

    if not isinstance(data, dict):
        return {
            "name": "observations:latest_shape",
            "ok": False,
            "detail": "latest observation root is not an object",
        }

    if not data:
        return {
            "name": "observations:latest_shape",
            "ok": False,
            "detail": "latest observation is empty",
        }

    keys = sorted(data.keys())
    return {
        "name": "observations:latest_shape",
        "ok": True,
        "detail": "keys=" + ", ".join(keys[:8]),
    }


def _observation_history_json_check():
    observations = ESTATE_ROOT / "observations"
    history = [
        path for path in sorted(observations.glob("ai_environment_*.json"))
        if not path.name.endswith("_latest.json")
    ]

    if not history:
        return {
            "name": "observations:history_json",
            "ok": False,
            "detail": "no timestamped observation files found",
        }

    invalid = []
    for path in history:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            invalid.append(f"{path.name}: {e}")

    return {
        "name": "observations:history_json",
        "ok": not invalid,
        "detail": f"{len(history)} valid historical observations" if not invalid else "; ".join(invalid[:3]),
    }


def _discovery_report_contract_check():
    result = _run(".\\estate.bat discovery-report")

    if not result["ok"]:
        return {
            "name": "observations:discovery_report_contract",
            "ok": False,
            "detail": result["stderr"] or result["stdout"],
        }

    output = result["stdout"]
    required_terms = [
        "Discovery",
        "AI",
        "Ollama",
    ]
    missing = [term for term in required_terms if term.lower() not in output.lower()]
    lines = [line for line in output.splitlines() if line.strip()]

    if missing:
        return {
            "name": "observations:discovery_report_contract",
            "ok": False,
            "detail": "missing report terms: " + ", ".join(missing),
        }

    if len(lines) < 5:
        return {
            "name": "observations:discovery_report_contract",
            "ok": False,
            "detail": f"report too short: {len(lines)} lines",
        }

    return {
        "name": "observations:discovery_report_contract",
        "ok": True,
        "detail": f"{len(lines)} non-empty lines",
    }



def _discovery_json_command_check():
    result = _run(".\\estate.bat discovery-report --json")
    if not result["ok"]:
        return {
            "name": "observations:discovery_report_json",
            "ok": False,
            "detail": result["stderr"] or result["stdout"],
        }

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {
            "name": "observations:discovery_report_json",
            "ok": False,
            "detail": str(e),
        }

    if not isinstance(data, dict):
        return {
            "name": "observations:discovery_report_json",
            "ok": False,
            "detail": "JSON report root is not an object",
        }

    return {
        "name": "observations:discovery_report_json",
        "ok": True,
        "detail": f"{len(data.keys())} top-level keys",
    }



def _discovery_status_command_check():
    result = _run(".\\estate.bat discovery-status --json")
    if not result["ok"]:
        return {
            "name": "observations:discovery_status_json",
            "ok": False,
            "detail": result["stderr"] or result["stdout"],
        }

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {
            "name": "observations:discovery_status_json",
            "ok": False,
            "detail": str(e),
        }

    required = [
        "exists",
        "changed_since_previous",
        "ollama_running",
        "ollama_models",
        "tools",
        "tts",
        "python_envs",
    ]
    missing = [key for key in required if key not in data]

    return {
        "name": "observations:discovery_status_json",
        "ok": not missing,
        "detail": "status keys present" if not missing else "missing: " + ", ".join(missing),
    }



def _discovery_catalog_schema_check():
    path = ESTATE_ROOT / "runtime" / "discovery" / "catalog.json"
    if not path.exists():
        return {
            "name": "observations:discovery_catalog_schema",
            "ok": False,
            "detail": "missing runtime/discovery/catalog.json",
        }

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {
            "name": "observations:discovery_catalog_schema",
            "ok": False,
            "detail": str(e),
        }

    if not isinstance(data, dict):
        return {
            "name": "observations:discovery_catalog_schema",
            "ok": False,
            "detail": "catalog root is not an object",
        }

    if data.get("version") != 1:
        return {
            "name": "observations:discovery_catalog_schema",
            "ok": False,
            "detail": "catalog version is not 1",
        }

    entities = data.get("entities")
    if not isinstance(entities, list):
        return {
            "name": "observations:discovery_catalog_schema",
            "ok": False,
            "detail": "entities is not a list",
        }

    ids = set()
    for index, entity in enumerate(entities):
        if not isinstance(entity, dict):
            return {
                "name": "observations:discovery_catalog_schema",
                "ok": False,
                "detail": f"entities[{index}] is not an object",
            }

        for field in ["id", "kind", "name", "first_seen", "last_seen", "observations", "status"]:
            if field not in entity:
                return {
                    "name": "observations:discovery_catalog_schema",
                    "ok": False,
                    "detail": f"entities[{index}] missing {field}",
                }

        if entity["id"] in ids:
            return {
                "name": "observations:discovery_catalog_schema",
                "ok": False,
                "detail": f"duplicate id: {entity['id']}",
            }

        ids.add(entity["id"])

    return {
        "name": "observations:discovery_catalog_schema",
        "ok": True,
        "detail": f"{len(entities)} catalog entities",
    }


def _discovery_catalog_command_check():
    result = _run(".\\estate.bat discovery-catalog --json")
    if not result["ok"]:
        return {
            "name": "observations:discovery_catalog_json",
            "ok": False,
            "detail": result["stderr"] or result["stdout"],
        }

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {
            "name": "observations:discovery_catalog_json",
            "ok": False,
            "detail": str(e),
        }

    return {
        "name": "observations:discovery_catalog_json",
        "ok": isinstance(data, dict) and "entities" in data,
        "detail": f"{len(data.get('entities', []))} entities" if isinstance(data, dict) else "catalog JSON root is not object",
    }


def _discovery_catalog_latest_coverage_check():
    latest_path = ESTATE_ROOT / "runtime" / "discovery" / "ai_environment_latest.json"
    catalog_path = ESTATE_ROOT / "runtime" / "discovery" / "catalog.json"

    try:
        latest = json.loads(latest_path.read_text(encoding="utf-8"))
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except Exception as e:
        return {
            "name": "observations:discovery_catalog_latest_coverage",
            "ok": False,
            "detail": str(e),
        }

    entities = catalog.get("entities", [])
    active_ids = {entity.get("id") for entity in entities if entity.get("status") == "active"}

    missing = []
    ollama = latest.get("ollama", {}) or {}
    if ollama.get("running") is not None and "provider:ollama" not in active_ids:
        missing.append("provider:ollama")

    for model in ollama.get("models", []) or []:
        if isinstance(model, dict):
            name = model.get("name") or model.get("model") or model.get("id")
        else:
            name = model
        expected = "model:" + str(name).strip().lower().replace("\\", "/")
        if expected not in active_ids:
            missing.append(expected)

    return {
        "name": "observations:discovery_catalog_latest_coverage",
        "ok": not missing,
        "detail": "latest Ollama entities represented" if not missing else "missing: " + ", ".join(missing[:5]),
    }



def _discovery_cycle_command_check():
    result = _run(".\\estate.bat discover --json")
    if not result["ok"]:
        return {
            "name": "observations:discovery_cycle_json",
            "ok": False,
            "detail": result["stderr"] or result["stdout"],
        }

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {
            "name": "observations:discovery_cycle_json",
            "ok": False,
            "detail": str(e),
        }

    required = [
        "version",
        "ok",
        "steps",
        "duration_seconds",
        "catalog_entities",
        "consecutive_successful_runs",
    ]
    missing = [key for key in required if key not in data]

    return {
        "name": "observations:discovery_cycle_json",
        "ok": not missing and data.get("ok") is True,
        "detail": "cycle metrics valid" if not missing else "missing: " + ", ".join(missing),
    }


def _discovery_metrics_file_check():
    path = ESTATE_ROOT / "runtime" / "discovery" / "metrics.json"
    if not path.exists():
        return {
            "name": "observations:discovery_metrics_file",
            "ok": False,
            "detail": "missing runtime/discovery/metrics.json",
        }

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {
            "name": "observations:discovery_metrics_file",
            "ok": False,
            "detail": str(e),
        }

    required = ["version", "started_at", "finished_at", "duration_seconds", "ok", "steps"]
    missing = [key for key in required if key not in data]

    return {
        "name": "observations:discovery_metrics_file",
        "ok": not missing and data.get("ok") is True,
        "detail": f"{len(data.get('steps', []))} cycle steps" if not missing else "missing: " + ", ".join(missing),
    }



def _discovery_refresh_command_check():
    result = _run(".\\estate.bat discovery-refresh --json")
    if not result["ok"]:
        return {
            "name": "observations:discovery_refresh_json",
            "ok": False,
            "detail": result["stderr"] or result["stdout"],
        }

    try:
        data = json.loads(result["stdout"])
    except Exception as e:
        return {
            "name": "observations:discovery_refresh_json",
            "ok": False,
            "detail": str(e),
        }

    required = ["ok", "cycle", "provider_sync", "status", "catalog_summary"]
    missing = [key for key in required if key not in data]

    return {
        "name": "observations:discovery_refresh_json",
        "ok": not missing and data.get("ok") is True,
        "detail": "refresh valid" if not missing else "missing: " + ", ".join(missing),
    }


def _history_checks():
    git_ec, git_result = _latest_git_ec()
    ledger_ec = _latest_ledger_ec()

    return [
        _ledger_structure_check(),
        _devlog_structure_check(),
        _latest_ledger_ec_in_devlog_check(),
        {
            "name": "history:latest_git_ec_matches_latest_ledger_ec",
            "ok": git_ec == ledger_ec,
            "detail": f"git={git_ec} ledger={ledger_ec}",
        },
    ]


def _git_checks():
    git_status = _run("git status --porcelain")
    return [
        {
            "name": "git:working_tree_clean",
            "ok": git_status["ok"] and git_status["stdout"] == "",
            "detail": git_status["stdout"],
        }
    ]


def run_audit():
    checks = []
    checks.extend(_run_check_group("syntax", _syntax_checks))
    checks.extend(_run_check_group("runtime", _runtime_checks))
    checks.extend(_run_check_group("json", _json_checks))
    checks.extend(_run_check_group("registry", _registry_checks))
    checks.extend(_run_check_group("observations", _observation_checks))
    checks.extend(_run_check_group("history", _history_checks))
    checks.extend(_run_check_group("git", _git_checks))

    passed = sum(1 for check in checks if check["ok"])
    failed = len(checks) - passed

    return {
        "version": 1,
        "passed": passed,
        "failed": failed,
        "checks": checks,
    }


def _check_group(name):
    if ":" in name:
        return name.split(":", 1)[0]
    return "estate"


def print_audit_report():
    report = run_audit()
    print("=========================================")
    print("Estate Audit Report")
    print("=========================================")
    print(f"Passed: {report['passed']}")
    print(f"Failed: {report['failed']}")
    print("")

    current_group = None
    for check in report["checks"]:
        group = _check_group(check["name"])
        if group != current_group:
            current_group = group
            print(f"[{current_group}]")

        mark = "PASS" if check["ok"] else "FAIL"
        print(f"{mark} | {check['name']}")
        if check["detail"]:
            print(f"     {check['detail']}")

    return report
